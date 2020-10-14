"""
This module contains miscellaneous functions.
"""

# Standard libraries
import random
import warnings
import logging
import logging.handlers
import os
import sys
import time
import typing
from pathlib import Path
import threading
import copy

logger = logging.getLogger(__name__)

# Azad libraries
from . import constants as Const
from .syntax import extensionSyntax


def barLine(message: str, lineLength: int = 120) -> str:
    """
    Print `<==...== msg ==...==>`.
    """
    if not isinstance(lineLength, int) or lineLength <= 20:
        raise ValueError("Invalid value lineLength = %s" % (lineLength,))
    baseMessage = "<" + "=" * (lineLength - 2) + ">"
    # 2x + msglen = total len
    preOffset = (lineLength - len(message)) // 2 - 1
    if preOffset <= 2:
        raise ValueError("Too long message for given line length")
    returnMessage = baseMessage[:preOffset] + " " + message + " "
    return returnMessage + baseMessage[-(lineLength - len(returnMessage)):]


def longEndSkip(message: str, maxLength: int = 100) -> str:
    """
    Print `msg ...` if message is too long.
    """
    assert maxLength > 3
    lenMsg = len(message)
    if lenMsg <= maxLength:
        return message
    else:
        return message[:maxLength - 3] + "..."


def randomName(length: int):
    """
    Return random name using English letters and numbers.
    Remind that calling this will reset random seed to arbitrary number.
    """
    random.seed(time.monotonic_ns())
    lowercases = "".join(chr(ord('a') + x) for x in range(26))
    numbers = "".join(chr(ord('0') + x) for x in range(10))
    candidates = lowercases + lowercases.upper() + numbers
    return "".join(random.choices(candidates, k=length))


def validateVerdict(
        verdictCount: typing.Mapping[Const.Verdict, int],
        *intendedCategories: typing.Tuple[Const.Verdict, ...]) -> bool:
    """
    Validate verdict with intended categories.
    """
    foundFeasibleCategories = set()  # This should be non-empty
    for category in verdictCount:
        if not isinstance(category, Const.Verdict):
            raise TypeError(
                "Invalid category type %s in verdictCount found" %
                (type(category),))
        elif verdictCount[category] == 0:
            continue
        elif category not in intendedCategories:  # Tolerate AC only
            if category is Const.Verdict.AC:
                continue
            else:
                return False
        else:
            foundFeasibleCategories.add(category)
    return bool(foundFeasibleCategories)


def setupLoggers(mainLogFilePath: Path, replaceOldHandlers: bool,
                 mainProcess: bool = True,
                 noStreamHandler: bool = False):
    """
    Set up loggers for Azad library.
    """
    rootLogger = logging.getLogger()

    # Helper function: Closing handler
    def closeHandler(oldHandler: logging.Handler):
        oldHandler.flush()
        oldHandler.close()
        rootLogger.removeHandler(oldHandler)

    # Cleanup
    if replaceOldHandlers:
        for oldHandler in rootLogger.handlers[::]:
            closeHandler(oldHandler)

    # Main file handler
    mainFileHandler = logging.handlers.RotatingFileHandler(
        filename=mainLogFilePath,
        maxBytes=Const.DefaultLogFileMaxSize,
        backupCount=Const.DefaultLogFileBackups
    )
    MFHformatter = logging.Formatter(
        Const.DefaultLogBaseFMT % (5000,), Const.DefaultLogDateFMT)
    mainFileHandler.setFormatter(MFHformatter)
    mainFileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(mainFileHandler)

    # Main stream handler
    if not noStreamHandler:
        if not mainProcess:
            warnings.warn(
                "Trying to initialize new stdout handler on non-main process.")

        # Still needed to replace stdout handler
        if not replaceOldHandlers:
            for oldHandler in rootLogger.handlers[::]:
                if isinstance(oldHandler, logging.StreamHandler) and \
                        oldHandler.stream is sys.stdout:
                    closeHandler(oldHandler)

        mainStreamHandler = logging.StreamHandler(sys.stdout)
        MSHformatter = logging.Formatter(
            Const.DefaultLogBaseFMT % (120,), Const.DefaultLogDateFMT)
        mainStreamHandler.setFormatter(MSHformatter)
        mainStreamHandler.setLevel(logging.INFO)
        rootLogger.addHandler(mainStreamHandler)

    # Final setup
    rootLogger.setLevel(logging.NOTSET)


def getAvailableTasksCount() -> int:
    """
    Get available CPU count for this process.
    If it's not available(like FreeBSD etc),
    then try to find physical number of CPUs.
    If physical number of CPUs is undeterminable, return 1 instead.
    """
    try:
        return max(len(os.sched_getaffinity(0)), 1)
    except AttributeError:
        count = os.cpu_count()
        return 1 if count is None else max(count // 2, 1)


def isExistingFile(path: Path) -> bool:
    """
    Check if given path is existing file.
    """
    if isinstance(path, str):
        path = Path(path)
    return isinstance(path, Path) and path.exists() and path.is_file()


def getExtension(path: typing.Union[str, Path]) -> typing.Union[str, None]:
    """
    Return given path's file extension if exists.
    """
    if isinstance(path, str):
        path = Path(path)
    filenameSplitted = path.name.split(".")
    if len(filenameSplitted) > 1 and \
            extensionSyntax.fullmatch(filenameSplitted[-1]):
        return filenameSplitted[-1]
    else:
        return None


def removeExtension(path: typing.Union[str, Path]) -> str:
    """
    Return given path's filename without extension.
    """
    if isinstance(path, str):
        path = Path(path)
    extension = getExtension(path)
    if extension is None:
        return path.name
    else:
        return path.name[:-(len(extension) + 1)]


def runThreads(func: typing.Callable[..., typing.Any],
               *argss: typing.Tuple[tuple, ...],
               timeout: float = None) -> float:
    """
    Run multiple threads on same function but different arguments.
    Return total time used to execute all threads.
    """
    threads = [threading.Thread(
        target=func, args=args, kwargs=kwargs) for (args, kwargs) in argss]
    startTime = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=timeout)
    endTime = time.perf_counter()
    return endTime - startTime


def pause(condition: str = "Q"):
    """
    Wait for user's response on standard input.
    This function is used for debug only.
    """
    condition = condition.upper().strip()
    q = input("Type '%s' and press enter to continue.. " % (condition,))
    while q.upper().strip() != condition:
        q = input()


def formatPathForLog(path: Path, maxDepth: int = 3) -> str:
    """
    Format given path to string for log file.
    """
    base = copy.deepcopy(path)
    for _ in range(maxDepth):
        base = base.parent
    return ("" if base is base.parent else "...") + \
        str(path.relative_to(base))


if __name__ == "__main__":

    print(longEndSkip(str([i for i in range(10**4)])))
