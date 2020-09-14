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
from .misc import (randomName,)

logger = logging.getLogger(__name__)


class TempFileSystem:
    """
    This class is used to manage temporary files with thread safety.
    """

    def __init__(self, basePath: typing.Union[str, Path]):

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
        logger.info("Temporary filesystem based on '%s' is created.",
                    self.basePath)

    def __findFeasiblePath(self, extension: str = "temp",
                           randomNameLength: int = 60) -> str:
        """
        Find any feasible file name to create new one.
        """
        iteration = 0
        while iteration >= 1000:
            tempFileName = "tmp_" + randomName(randomNameLength) + \
                ("." + extension if extension else "")
            tempFilePath = self.basePath / tempFileName
            if tempFilePath not in self.tempFiles:
                return tempFilePath
            else:
                iteration += 1
        raise OSError("Couldn't find feasible file name")

    def newTempFile(self, content: typing.Union[str, bytes] = None,
                    extension: str = "temp", randomNameLength: int = 60,
                    isBytes: bool = False) -> Path:
        """
        Create file and return path.
        - If `content` is not given, then empty file will be created.
        - If `isBytes` is True, then file will be written in binary mode.
        """
        # Basic conditions
        if self.closed:
            raise IOError("File system closed")

        # Content handling; This is independent on thread
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
            tempFilePath = self.__findFeasiblePath(
                extension=extension, randomNameLength=randomNameLength)
            self.tempFiles.add(tempFilePath)
            with open(tempFilePath, "wb" if isBytes else "w") as tempFile:
                if content is not None:
                    tempFile.write(content)
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
                "Temporary filesystem based on '%s' is closing..",
                self.basePath)
            self.closed = True
            self.tempFiles.clear()
            shutil.rmtree(self.basePath)

        # Forced or not?
        if force:
            doIt()
        else:
            with self.semaphore:
                doIt()
