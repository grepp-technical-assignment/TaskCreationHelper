"""
This module contains miscellaneous functions.
"""

# Standard libraries
import random
import warnings
import logging
import os
import sys
import time
import typing
from pathlib import Path

# Azad libraries
from . import constants as Const


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
        verdictCount: dict,
        intendedCategories: typing.List[Const.SolutionCategory]) -> bool:
    """
    Validate verdict with intended categories.
    """
    # Fill unfilled categories
    for category in intendedCategories:
        if category not in verdictCount:
            verdictCount[category] = 0

    # Check
    foundFeasibleCategories = set()  # This should not be empty
    for category in verdictCount:
        if not isinstance(category, Const.SolutionCategory):
            raise TypeError(
                "Invalid category type %s in verdictCount found" %
                (type(category),))
        elif verdictCount[category] == 0:
            continue
        elif category not in intendedCategories:  # Tolerate AC only
            if category is Const.SolutionCategory.AC:
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


def getAvailableCPUCount() -> typing.Union[int, None]:
    """
    Get available CPU count for this process.
    If it's not available(like FreeBSD etc),
    then try to find physical number of CPUs.
    If physical number of CPUs is undeterminable, return None instead.
    """
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count()


if __name__ == "__main__":
    print(longEndSkip(str([i for i in range(10**4)])))
