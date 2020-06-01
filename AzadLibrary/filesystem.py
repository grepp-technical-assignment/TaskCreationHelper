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
import json

# Azad libraries
from .misc import (randomName,)


class TempFileSystem:
    """
    This class is used to manage temporary files.
    This is not threadsafe.
    """

    def __init__(self, basePath: typing.Union[str, Path]):
        while True:
            self.basePath: Path = Path(basePath) / \
                ("tempfilesystem_" + randomName(20))
            if not self.basePath.exists():
                break
        self.basePath.mkdir()
        self.tempfiles: typing.Set[Path] = set()
        self.closed = False
        atexit.register(self.close)

    def newTempFile(self, content: typing.Union[str, bytes] = None,
                    extension: str = "temp", randomLength: int = 60,
                    b: bool = False, isJson: bool = False) -> Path:
        """
        Create file and return path.
        - If `content` is not given, then empty file will be created.
        - If `b` is True, then file will be written in binary mode.
        - If `isJson` is True, then content will be dumped into file by json module.
        """
        if self.closed:
            raise IOError("File system closed")
        elif b and isJson:
            raise ValueError("Trying json mode and binary mode together")

        # Content handling
        if content is None or isJson:
            pass
        elif b:
            if isinstance(content, (bytes, bytearray)):
                pass
            else:
                content = str(content).encode()
        else:
            if isinstance(content, (bytes, bytearray)):
                content = content.decode()
            else:
                content = str(content)

        # Find feasible filename
        while True:
            tempFilePath = self.basePath / \
                ("tmp_" + randomName(randomLength) + "." + extension)
            if tempFilePath not in self.tempfiles:
                break

        # Actual file creation
        self.tempfiles.add(tempFilePath)
        with open(tempFilePath, "w" if not b else "wb") as tempFile:
            if content is not None:
                if isJson:
                    json.dump(content, tempFile)
                else:
                    tempFile.write(content)
        return tempFilePath

    def pop(self, filePath: typing.Union[str, Path], b: bool = False) \
            -> typing.Union[bytes, str]:
        """
        Read a content from given temp file and remove it.
        If given temp file is already deleted, then tolerate it instead of raising `FileNotFoundError`.
        - `b` determines rb mode(True) or r mode(False, default).
        """
        if filePath not in self.tempfiles:
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

    def close(self):
        """
        Shutdown this temp file system and remove all associated files.
        """
        if self.closed:
            return
        self.closed = True
        self.tempfiles.clear()
        shutil.rmtree(self.basePath)
