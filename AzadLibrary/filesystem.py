"""
This module supports high level management of files.
"""

# Standard libraries
import typing
from pathlib import Path
import os
import shutil
import atexit
import threading
import logging

# Azad libraries
from .misc import randomName, formatPathForLog

logger = logging.getLogger(__name__)


class TempFileSystem:
    """
    This class is used to manage temporary files with thread safety.
    """

    def __init__(self, basePath: typing.Union[str, Path]):

        # BasePath should exists
        if not basePath.exists() or basePath.is_file():
            raise NotADirectoryError("Invalid path '%s'" % (basePath,))

        # Make new temporary folder
        while True:
            self.basePath: Path = Path(basePath) / \
                ("tempfilesystem_" + randomName(20))
            if not self.basePath.exists():
                break
        self.basePath.mkdir()

        # Setup attributes
        self.tempFiles: typing.Set[Path] = set()
        self.semaphore = threading.BoundedSemaphore()
        self.closed = False

        # Extra
        atexit.register(self.close, force=True)
        logger.info("Temporary filesystem based on \"%s\" is created.",
                    formatPathForLog(self.basePath))

    def __findFeasiblePath(
            self, extension: str = "temp", randomNameLength: int = None,
            namePrefix: str = None) -> str:
        """
        Find any feasible file name to create new one.
        This method is not threadsafe.
        """
        namePrefix = "" if not namePrefix else namePrefix + "_"
        randomNameLength = 30 if not randomNameLength else randomNameLength
        iteration, iterLimit = 0, 10 ** 3
        while iteration < iterLimit:
            tempFileName = namePrefix + randomName(randomNameLength) + \
                ("." + extension if extension else "")
            tempFilePath = self.basePath / tempFileName
            if tempFilePath not in self.tempFiles:
                return tempFilePath
            else:
                iteration += 1
        raise OSError("Couldn't find feasible file name")

    def newTempFile(self, content: typing.Union[str, bytes] = None,
                    filename: str = None, extension: str = "temp",
                    randomNameLength: int = None, isBytes: bool = False,
                    namePrefix: str = None) -> Path:
        """
        Create file and return path.
        - If `content` is not given, then empty file will be created.
        - If `isBytes` is True, then file will be written in binary mode.
        """
        # Basic conditions
        if self.closed:
            raise OSError("File system closed")

        # Content handling; This is independent so can be executed directly
        if content is None:
            pass
        elif isBytes:  # Encode content
            if not isinstance(content, (bytes, bytearray)):
                content = str(content).encode()
        else:  # Decode content
            if isinstance(content, (bytes, bytearray)):
                content = content.decode()
            else:
                content = str(content)

        # Actual file creation
        with self.semaphore:
            if filename is not None:
                tempFilePath = self.basePath / \
                    (filename + (("." + extension) if extension else ""))
                if tempFilePath in self.tempFiles:
                    raise OSError(
                        "Filename '%s' already exists" % (tempFilePath.name,))
            else:
                tempFilePath = self.__findFeasiblePath(
                    extension=extension, randomNameLength=randomNameLength,
                    namePrefix=namePrefix)
            self.tempFiles.add(tempFilePath)
            with open(tempFilePath, "wb" if isBytes else "w") as tempFile:
                if content is not None:
                    tempFile.write(content)

        logger.debug(
            "Temp file \"%s\" created.", formatPathForLog(tempFilePath))
        return tempFilePath

    def copy(self, origin: typing.Union[str, Path],
             destination: str = None, extension: str = "temp",
             randomNameLength: int = None, namePrefix: str = None) -> Path:
        """
        Copy the external file into current temp file system.
        """
        # Since we read only, it's ok to read this file directly
        with self.semaphore:
            if destination is not None:
                tempFilePath = self.basePath / \
                    (destination + (("." + extension) if extension else ""))
                if tempFilePath in self.tempFiles:
                    raise OSError(
                        "Filename '%s' already exists" % (tempFilePath.name,))
            else:
                tempFilePath = self.__findFeasiblePath(
                    extension=extension, randomNameLength=randomNameLength,
                    namePrefix=namePrefix)
            shutil.copyfile(origin, tempFilePath)

        logger.debug("Temp file \"%s\" created by copying from \"%s\".",
                     formatPathForLog(tempFilePath), formatPathForLog(origin))
        return tempFilePath

    def pop(self, filePath: typing.Union[str, Path], b: bool = False) \
            -> typing.Union[bytes, str, None]:
        """
        Read a content from given temp file and remove it.
        If given temp file is already deleted, then tolerate it instead of raising `FileNotFoundError`.
        - `b` determines rb mode(True) or r mode(False, default).
        """
        # Basic conditions
        if self.closed:
            raise IOError("File system closed")

        # Erase the file
        if isinstance(filePath, str):
            filePath = Path(filePath)
        with self.semaphore:
            if filePath not in self.tempFiles:
                raise FileNotFoundError(
                    "Couldn't find '%s' among registered temp files" % (filePath,))
            try:
                with open(filePath, "r" if not b else "rb") as tempfile:
                    result = tempfile.read()
                os.remove(filePath)
            except FileNotFoundError:
                pass
            else:
                logger.debug("Temp file \"%s\" popped.",
                             formatPathForLog(filePath))
                return result

    def close(self, force: bool = False):
        """
        Shutdown this temp file system and remove all associated files.
        """
        # Already closed
        if self.closed:
            return

        # Actual termination process
        def doIt():
            logger.info(
                "Temporary filesystem based on \"%s\" is closing..",
                formatPathForLog(self.basePath))
            self.closed = True
            self.tempFiles.clear()
            shutil.rmtree(self.basePath)

        # Forced or not?
        if force:
            doIt()
        else:
            with self.semaphore:
                doIt()
