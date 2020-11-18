"""
This module supports high level functionalities of file system.
"""

# Standard libraries
import threading
from pathlib import Path
import atexit
import typing
import shutil
import warnings
import os

# Azad libraries
from .constants import NullSemaphore
from .misc import randomName, formatPathForLog
from .errors import TempFileSystemClosed


def TFSThreadSafe(method):
    """
    Threadsafe decorator for TempFileSystem.
    """

    def innerFunc(self, *args, force: bool = False, **kwargs):
        with (self.semaphore if not force else NullSemaphore):
            return method(self, *args, **kwargs)
    return innerFunc


def checkIfClosed(method):
    """
    Closed checking decorator for TempFileSystem.
    """

    def innerFunc(self, *args, **kwargs):
        if self.closed:
            warnings.warn("This file system is already closed",
                          TempFileSystemClosed)
        else:
            return method(self, *args, **kwargs)
    return innerFunc


def checkBasePath(method):
    """
    Check if given path is inside of TempFileSystem's path.
    If basePath is not given, then `basePath := self.path`.
    """

    def innerFunc(self, *args, basePath: Path = None, **kwargs):
        if basePath is not None:
            if not basePath.relative_to(self.path):
                raise OSError(
                    "Given basePath \"%s\" is not inside of TFS path \"%s\"" %
                    (basePath, self.path))
        else:
            basePath = self.path
        return method(self, *args, basePath=basePath, **kwargs)
    return innerFunc


class TempFileSystem:
    """
    Supports temporary file system by path.
    """

    DefaultRandomNameLength = 8
    DefaultRandomTryIterationLimit = 10 ** 3

    def __init__(self, *args, **kwargs):

        # Core path
        self.path = Path(*args, **kwargs)
        if not self.path.exists():
            self.path.mkdir()
        elif self.path.is_file():
            raise NotADirectoryError("Invalid path \"%s\"" % (self.path,))

        # Other attributes
        self.semaphore = threading.BoundedSemaphore()
        self.childs = set()
        self.closed = False
        atexit.register(self.close, force=True)

    def __str__(self):
        return "Temp file system at \"%s\"" % \
            (formatPathForLog(self.path),)

    def __truediv__(self, name: str) -> Path:
        return self.path / name

    @staticmethod
    def getName(name: str, extension: str = None,
                namePrefix: str = None) -> str:
        """
        Get complete file/directory name with given prefix and extension.
        """
        if namePrefix is not None:
            prefix = namePrefix + "_"
        else:
            prefix = ""
        suffix = ("." + extension if extension is not None else "")
        return prefix + name + suffix

    def contains(self, name: typing.Union[str, Path]):
        """
        Return true if there is any file/folder
        with same name in this file system.
        """
        if isinstance(name, str):
            return (self.path / name).exists()
        elif isinstance(name, Path):
            return name.exists() and name.relative_to(self.path)
        else:
            raise TypeError("Invalid name type %s" % (type(name),))

    @checkBasePath
    def __findFeasiblePath(
            self, extension: str = None, namePrefix: str = None,
            randomNameLength: int = None, basePath: Path = None) -> Path:
        """
        Find any feasible path for new file or folder's name.
        """

        length = self.DefaultRandomNameLength \
            if randomNameLength is None else randomNameLength

        for _ in range(self.DefaultRandomTryIterationLimit):
            tempPath = basePath / self.getName(
                randomName(length), extension=extension,
                namePrefix=namePrefix)
            if not self.contains(tempPath):
                return tempPath
        raise OSError("Couldn't find feasible path in %d iterations" %
                      (self.DefaultRandomTryIterationLimit,))

    @checkIfClosed
    @checkBasePath
    @TFSThreadSafe
    def newTempFile(
            self, content: typing.Union[str, bytes] = None,
            name: str = None, extension: str = None,
            namePrefix: str = None, basePath: Path = None) -> Path:
        """
        Make new file under this directory.
        """
        wmode: str = "wb" if isinstance(content, bytes) else "w"

        # Determine name
        if name is not None:
            path = basePath / self.getName(
                name, extension=extension, namePrefix=namePrefix)
            if self.contains(path):
                raise FileExistsError
        else:
            path = self.__findFeasiblePath(
                extension=extension, namePrefix=namePrefix,
                basePath=basePath)

        # Write content and return
        with open(path, wmode) as file:
            if content is not None:
                file.write(content)
        return path

    @checkIfClosed
    @checkBasePath
    @TFSThreadSafe
    def newFolder(self, name: str = None, namePrefix: str = None,
                  basePath: Path = None) -> Path:
        """
        Make new folder under this directory.
        If name is not None, then the depth will be ignored.
        """
        # Determine path
        if name is not None:
            path = basePath / self.getName(name, namePrefix=namePrefix)
            if self.contains(path):
                raise OSError("Directory already exists")
        else:
            path = self.__findFeasiblePath(
                namePrefix=namePrefix, basePath=basePath)

        path.mkdir()
        return path

    @checkIfClosed
    @checkBasePath
    @TFSThreadSafe
    def copyFile(self, source: typing.Union[str, Path],
                 destName: str = None, extension: str = None,
                 namePrefix: str = None, basePath: Path = None) -> Path:
        """
        Copy external file into current TempFileSystem.
        """
        if isinstance(source, str):
            source = Path(source)
        if not source.exists() or not source.is_file():
            raise FileNotFoundError

        # Get name
        if destName is not None:
            path = basePath / self.getName(
                destName, extension=extension, namePrefix=namePrefix)
            if self.contains(path):
                raise FileExistsError
        else:
            path = self.__findFeasiblePath(
                extension=extension, namePrefix=namePrefix,
                basePath=basePath)

        # Fast copy using shutil
        shutil.copyfile(source, path)
        return path

    @checkIfClosed
    @TFSThreadSafe
    def pop(self, path: typing.Union[str, Path], b: bool = True) -> \
            typing.Union[str, bytes, None]:
        """
        Delete file or folder by given name.
        If given name is file, return file content.
        """
        if isinstance(path, str):
            path: Path = self.path / path
        elif isinstance(path, Path):
            pass
        else:
            raise TypeError("Invalid name type %s" % (type(path),))

        if not self.contains(path):
            raise FileNotFoundError("name = %s" % (path,))
        elif path.is_file():  # File
            with open(path, "rb" if b else "r") as file:
                content = file.read()
            os.remove(path)
            return content
        else:  # Directory
            shutil.rmtree(path)
            return None

    @checkIfClosed
    @TFSThreadSafe
    def close(self):
        """
        Close file system by deleting everything.
        """
        self.closed = True
        shutil.rmtree(self.path)
