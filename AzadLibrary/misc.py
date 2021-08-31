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
import statistics
import resource

logger = logging.getLogger(__name__)

# Azad libraries
from . import constants as Const
from .syntax import extensionSyntax
from .errors import AzadError


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


def randomName(length: int) -> str:
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


def setupLoggers(
        mainLogFilePath: Path, replaceOldHandlers: bool,
        mainProcess: bool = True,
        noStreamHandler: bool = False,
        logLevel: int = logging.NOTSET):
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
    rootLogger.setLevel(logLevel)


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


def runThreads(
    func: typing.Callable[..., typing.Any],
    concurrencyLimit: int,
    *argss: typing.Tuple[tuple, ...],
    timeout: float = None,
    funcName: str = "unknown") \
        -> typing.Tuple[float, typing.List[float]]:
    """
    Run multiple threads on same function but different arguments.
    """

    # Semaphore and execution time measure
    semaphore = threading.BoundedSemaphore(concurrencyLimit)
    dtDistribution = [None for _ in range(len(argss))]

    def tempFunc(index, *args, **kwargs):
        """
        Temporary function which runs given function,
        but with several additional functionalities.
        """
        with semaphore:
            logger.debug("Running %s #%d..", funcName, index + 1)
            startTime = time.perf_counter()
            func(*args, **kwargs)
            endTime = time.perf_counter()
            logger.debug("Finishing %s #%d in %gs.. (Global dt)",
                         funcName, index + 1, endTime - startTime)
        dtDistribution[index] = endTime - startTime

    # Make, run, and join threads
    threads = [threading.Thread(
        target=tempFunc, args=(i,) + args, kwargs=kwargs)
        for (i, (args, kwargs)) in enumerate(argss)]
    startTime = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=timeout)
    endTime = time.perf_counter()
    return (endTime - startTime, dtDistribution)


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


def getLimitResourceFunction(TL: float, ML: float) \
        -> typing.Callable[..., None]:
    """
    Return function which limits current process's
    soft time limit and soft memory limit.
    All errors will be dropped.
    """
    def func():
        import resource

        # Setting CPU time limit
        _, hardTL = resource.getrlimit(resource.RLIMIT_CPU)
        resource.setrlimit(
            resource.RLIMIT_CPU, (max(1, round(TL)), hardTL))

        # Setting total memory amount
        for rid in (resource.RLIMIT_AS, resource.RLIMIT_DATA,
                    resource.RLIMIT_STACK):
            try:
                _, hardML = resource.getrlimit(rid)
                resource.setrlimit(rid, (round(ML * (1 << 20)), hardML))
            except (OSError, ValueError):
                pass

    return func


def prlimitSubprocessResource(pid: int, TL: float, ML: float):
    """
    Use prlimit directly to limit specific process's
    soft time limit and soft memory limit.
    """
    _, hardTL = resource.prlimit(pid, resource.RLIMIT_CPU)
    resource.prlimit(pid, resource.RLIMIT_CPU, (max(1, round(TL)), hardTL))

    for rid in (resource.RLIMIT_AS, resource.RLIMIT_DATA,
                resource.RLIMIT_STACK):
        try:
            _, hardML = resource.prlimit(pid, rid)
            resource.prlimit(pid, rid, (round(ML * (1 << 20)), hardML))
        except (OSError, ValueError):
            pass


def reportSolutionStatistics(
        verdicts: typing.List[Const.Verdict],
        dtDistribution: typing.List[float],
        quantilesCount: int = 4) -> None:
    """
    Report statistics based on verdicts and dt distribution.
    """

    # Brief report first
    logger.info("Verdict brief: %s", " / ".join("%s %g%%" % (
        verdict.name, 1e2 * verdicts.count(verdict) / len(verdicts))
        for verdict in Const.Verdict)
    )
    if len(dtDistribution) > 1:
        dtQuantiles = statistics.quantiles(dtDistribution, n=quantilesCount)
        dtQuantiles = [min(dtDistribution)] + \
            dtQuantiles + [max(dtDistribution)]
        logger.info("DT brief (not precise): %s", " / ".join("Q%d %gs" % (
            i, dtQuantiles[i]) for i in range(len(dtQuantiles))))

    # Detail individuals
    logger.debug("Verdicts: [%s]", ", ".join(v.name for v in verdicts))
    logger.debug("DT distribution: [%s]", ", ".join(
        "%gs" % (dt,) for dt in dtDistribution))


def reportCompilationFailure(
        errLogPath: Path, modulePath: Path,
        args: typing.List[typing.Union[str, Path]],
        moduleType: Const.SourceFileType):
    """
    Report compilation failure.
    """
    newArgs = [formatPathForLog(arg) if isinstance(arg, Path)
               else arg for arg in args]
    with open(errLogPath, "r") as errLogFile:
        logger.error(
            "Compilation failure on %s \"%s\"; args = %s, log =\n%s",
            moduleType.name, formatPathForLog(modulePath),
            newArgs, errLogFile.read())
        raise AzadError(
            "Compilation failure on %s \"%s\"; args = %s" %
            (moduleType.name, formatPathForLog(modulePath), newArgs))


if __name__ == "__main__":

    print(longEndSkip(str([i for i in range(10**4)])))
