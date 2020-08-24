"""
This module provides advanced multiprocessing functionalities.
"""

# Standard libraries
from math import inf
import typing
from pathlib import Path
import time
import os
import threading
import multiprocessing
import json
import traceback
import resource
import logging

logger = logging.getLogger(__name__)

# Azad libraries
from .errors import AzadTLE
from .constants import (
    SourceFileType,
    ExitCodeSuccess, ExitCodeTLE, ExitCodeMLE,
    ExitCodeFailedToReturnData,
    ExitCodeFailedInAVPhase, ExitCodeFailedInBPPhase,
    ExitCodeFailedInLoopPhase,
)
from .externalmodule import prepareExecFunc
from .misc import (randomName, getAvailableCPUCount)
from .iodata import (checkDataType, checkDataCompatibility)

# Context of spawning process instead of forking
SpawnContext = multiprocessing.get_context('spawn')


class BaseAzadProcess(SpawnContext.Process):
    """
    Process with basic functionalities.
    To prevent unexpected deadlocks, I use SpawnProcess as parent class.

    Features:
    1. If given timelimit exceeds, then the process will be automatically terminated.
    2. Return PGized data in JSON format.
    """
    minDT = 1 / 20
    maxDT = 100

    def __init__(self, *args__, timelimit: float = None, memlimit: float = None,
                 outFilePath: typing.Union[Path, str] = None,
                 outFileExistenceToleration: bool = True,
                 **kwargs__):
        """
        If `timelimit` is given, then the process will automatically terminates after execution.
        If `outFilePath` is given, then the result will be outputted into file with json/traceback format.
            Give this argument only if when your function returns primitive type only.
        If `memlimit` is given, then the process will automatically
        """

        super().__init__(*args__, **kwargs__)

        # Time limit
        self.timelimit = timelimit if timelimit is not None else inf
        if not (self.timelimit == inf or
                isinstance(self.timelimit, (int, float))):
            raise TypeError("Invalid timelimit %s given." % (timelimit,))
        elif self.timelimit <= 0:
            raise ValueError(
                "Non-positive timelimit %gs given." % (self.timelimit,))

        # Memory limit
        self.memlimit: int = memlimit if memlimit is None \
            else round(memlimit * (2 ** 20))

        # Json Outfile
        self.outFilePath = Path(outFilePath) if outFilePath else None
        if self.outFilePath and self.outFilePath.exists():
            if not outFileExistenceToleration:
                raise OSError("Target file '%s' already exists" %
                              (self.outFilePath,))

        # Misc
        self.outfileCleaned = False
        self.resultJson = None

    def getCapsule(self):
        """
        Get capsulized function to execute in loop phase.
        This method can be overrided in subclasses.
        Capsule function should catch and record raised exception internally,
        otherwise the process will exit successfully.
        """
        def func(*args, **kwargs):
            nonlocal self
            try:
                self.capsuleResult = self._target(*self._args, **self._kwargs)
            except BaseException as err:
                self.capsuleException = err
        return func

    def internalPhaseBeforePreparation(self):
        """
        This is one of execution phases.
        In this phase, process prepares something needed.
        """
        pass

    def internalPhaseLoop(self):
        """
        This is one of execution phases.
        In this phase, process executes target function under TLE.
        """
        self.capsuleResult = None
        self.capsuleException: Exception = None
        mainThread = threading.Thread(
            target=self.getCapsule(),
            args=self._args, kwargs=self._kwargs,
            daemon=True)
        startTime = time.process_time()
        try:
            mainThread.start()
            while True:
                age = time.process_time() - startTime
                if age >= self.timelimit:
                    raise AzadTLE("Time limit %gs expired." %
                                  (self.timelimit))
                elif not mainThread.is_alive():
                    break
                else:
                    time.sleep(self.minDT)
        except AzadTLE:  # TLE
            exit(ExitCodeTLE)
        else:
            self.executedTime = time.process_time() - startTime

    def internalPhaseAfterValidation(self) -> int:
        """
        This is one of execution phases.
        In this phase, process validates returned data.
        Don't confuse this with `validator`, two concepts are different.

        Return value must be `None` or `int` - which will be used for return code.
        Override this method in child class to do custom after-validation.
        """
        pass

    def internalPhaseWriteOutFile(self):
        """
        This is one of execution phases.
        In this phase, process writes returned value or raised exception
        to send data to the parent process.
        """
        try:
            if self.outFilePath:
                with open(self.outFilePath, "w") as outFile:
                    if self.capsuleException is None:
                        json.dump({
                            "result": self.capsuleResult,
                            "executedTime": self.executedTime,
                        }, outFile)
                    else:
                        assert isinstance(self.capsuleException, BaseException)
                        json.dump({
                            "traceback": "".join(traceback.format_exception(
                                type(self.capsuleException),
                                self.capsuleException,
                                self.capsuleException.__traceback__
                            )),
                            "executedTime": self.executedTime,
                        }, outFile)
        except Exception:  # Failed to return data
            exit(ExitCodeFailedToReturnData)

    def limitRAM(self, newSoft: int = None):
        """
        Limit ram of created process.
        If `newSoft` is None, then the original hard limit will be applied.
        """
        oldSoft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS,
                           (hard if newSoft is None else newSoft, hard))

    def run(self):
        """
        Actual execution process.
        Function return result will be `self.capsuleResult`.
        Raised exception will be `self.capsuleException`.
        """
        self.limitRAM(self.memlimit)  # Resource limitation

        # Before-preparation phase (BP phase)
        try:
            self.internalPhaseBeforePreparation()
        except Exception as err:
            self.capsuleException = err
            self.internalPhaseWriteOutFile()
            exit(ExitCodeFailedInBPPhase)

        # Looping phase; TLE will exit here
        self.internalPhaseLoop()
        if self.capsuleException is not None:
            self.internalPhaseWriteOutFile()
            if isinstance(self.capsuleException, MemoryError):
                exit(ExitCodeMLE)
            elif isinstance(self.capsuleException, OSError) and \
                    self.capsuleException.errno == 12:
                exit(ExitCodeMLE)
            else:
                exit(ExitCodeFailedInLoopPhase)

        # After-validation phase (AV phase)
        try:
            self.internalPhaseAfterValidation()
        except Exception as err:
            self.capsuleException = err
            self.internalPhaseWriteOutFile()
            exit(ExitCodeFailedInAVPhase)
        else:
            self.internalPhaseWriteOutFile()
            exit(ExitCodeSuccess)

    def cleanOutFile(self):
        """
        Clean external files which are used by process.
        This method should be runned by parent process of this.
        Take `self.returnedValue` as returned value from process target.
        """
        if self.is_alive():
            raise Exception(
                "Tried to clean outfiles before process terminated.")
        elif self.outfileCleaned:
            return
        elif not (self.outFilePath and self.outFilePath.exists()
                  and self.outFilePath.is_file()):
            return

        # Proceed
        self.outfileCleaned = True
        with open(self.outFilePath, "r") as outFile:
            self.resultJson = json.load(outFile)
        os.remove(self.outFilePath)

        # Mark as cleaned
        self.outfileCleaned = True

    def join(self, timeout: float = None):
        super().join(timeout=timeout)
        if not self.is_alive():
            self.cleanOutFile()

    def terminate(self):
        super().terminate()
        self.cleanOutFile()

    def kill(self):
        super().kill()
        self.cleanOutFile()


class AzadProcessForModules(BaseAzadProcess):
    """
    Abstract base of AzadProcess for external modules.
    Since we can't send non-global function to spawned process (unpicklable),
    we take function which generates real function from module instead,
    and replace target by that real function.
    """

    def __init__(self,
                 sourceFilePath: typing.Union[str, Path],
                 sourceFileType: SourceFileType, *args__,
                 timelimit: float = None, memlimit: float = None,
                 **kwargs__):
        """
        You should not give `target` as parameter.
        You should give `timelimit` and `memlimit` as parameter,
        because external module function should have time limit to execute.
        """

        if "target" in kwargs__:
            raise ValueError("target should not be given.")
        elif timelimit is None:
            raise ValueError("timelimit should be specified.")
        elif memlimit is None:
            raise ValueError("memlimit should be specified.")
        super().__init__(*args__, target=None, timelimit=timelimit,
                         memlimit=memlimit, **kwargs__)
        self.sourceFilePath = Path(sourceFilePath)
        self.sourceFileType = sourceFileType

    def getCapsule(self):
        """
        Generate and call module function instead of just calling `self._target`.
        """
        moduleFunc = prepareExecFunc(self.sourceFilePath, self.sourceFileType)

        def func(*args, **kwargs):
            nonlocal self, moduleFunc
            try:
                self.capsuleResult = moduleFunc(*self._args, **self._kwargs)
            except Exception as err:
                self.capsuleException = err
        return func


class AzadProcessGenerator(AzadProcessForModules):
    """
    AzadProcess used for generators.
    """

    def __init__(self, sourceFilePath: typing.Union[str, Path],
                 args: typing.List[str], parameters: dict, *args__,
                 outFilePath: typing.Union[str, Path] = None, **kwargs__):
        """
        For `args`, give list of strings. It will be automatically converted.
        For `parameters`, give `AzadCore.parameters`.
        If outFilePath is not given, then process will generate random name.
        """
        if outFilePath is None:
            outFilePath = "generator_process_" + randomName(64) + ".temp"
        super().__init__(
            sourceFilePath, SourceFileType.Generator,
            *args__, args=[args], outFilePath=outFilePath, **kwargs__)

        # Parameter info; Will be used in after-validation phase.
        self.parameters = parameters

    def getCapsule(self):
        """
        Set random seed before calling actual capsulized function.
        """
        target = super().getCapsule()

        def func(args: typing.List[str]):
            nonlocal self, target
            import random
            import hashlib
            hashValue = hashlib.sha256("|".join(args).encode()).hexdigest()
            random.seed(hashValue)
            target(args)
        return func

    def internalPhaseAfterValidation(self):
        """
        Validate if generated result is fit for target parameters.
        """
        assert isinstance(self.capsuleResult, dict)
        assert set(self.capsuleResult.keys()) == set(self.parameters.keys())
        for name in self.parameters:
            assert checkDataType(
                self.capsuleResult[name], self.parameters[name]["type"],
                self.parameters[name]["dimension"])
            assert checkDataCompatibility(
                self.capsuleResult[name], self.parameters[name]["type"])


class AzadProcessValidator(AzadProcessForModules):
    """
    AzadProcess used for validators.
    Don't confuse concept of `Validator` and internal phase `AfterValidation`.
    """

    def __init__(
            self, sourceFilePath: typing.Union[str, Path],
            inputDataFilePath: typing.Union[str, Path],
            *args__, **kwargs__):
        """
        Do not give `args`, `kwargs` parameters directly.
        Instead, send data by JSON file(parameter `inputDataFilePath`).
        I recommend you to give `inputDataFilePath` generated by `TempFileSystem`.
        `inputDataFilePath` will be also used as `outFilePath`.
        """
        if 'args' in kwargs__ or 'kwargs' in kwargs__:
            raise ValueError("Do not give args or kwargs as parameter.")
        super().__init__(
            sourceFilePath, SourceFileType.Validator, *args__,
            outFilePath=Path(inputDataFilePath), **kwargs__)

    def internalPhaseBeforePreparation(self):
        """
        Receive data using external json file.
        """
        with open(self.outFilePath, "r") as jsonFile:
            self._args = json.load(jsonFile)
            self._kwargs = {}


class AzadProcessSolution(AzadProcessForModules):
    """
    AzadProcess used for solutions.
    """

    def __init__(
            self, sourceFilePath: typing.Union[str, Path],
            inputDataFilePath: typing.Union[str, Path],
            returnValueInfo: dict, *args__, **kwargs__):
        """
        `inputDataFilePath` will be also used as `outFilePath`.
        For `returnValueInfo`, give `AzadCore.returnValueInfo`.
        """
        if 'args' in kwargs__ or 'kwargs' in kwargs__:
            raise ValueError("Do not give args or kwargs as parameter.")
        super().__init__(
            sourceFilePath, SourceFileType.Solution,
            outFilePath=inputDataFilePath, *args__, **kwargs__)

        # Return value info
        self.returnValueInfo = returnValueInfo

    def internalPhaseBeforePreparation(self):
        """
        Receive data using external json file.
        """
        with open(self.outFilePath, "r") as jsonFile:
            self._args = json.load(jsonFile)
            self._kwargs = {}

    def internalPhaseAfterValidation(self):
        """
        Validate if generated result is fit for target return value.
        """
        assert checkDataType(
            self.capsuleResult, self.returnValueInfo["type"],
            self.returnValueInfo["dimension"])
        assert checkDataCompatibility(
            self.capsuleResult, self.returnValueInfo["type"])


def work(*processes: typing.List[BaseAzadProcess],
         maxConcurrentCount: int = None,
         processNamePrefix: str = None):
    """
    Run given processes, but with bounded amount of concurrent processes.
    """
    # Check max concurrent count
    if maxConcurrentCount is None:
        maxConcurrentCount = getAvailableCPUCount()
        if maxConcurrentCount is None:  # Even if CPU count is available?
            maxConcurrentCount = 4
    assert maxConcurrentCount > 0
    boundedSemaphore = threading.BoundedSemaphore(
        maxConcurrentCount - 1 if maxConcurrentCount > 1 else 1)

    # This function will be used in each process with semaphore.
    def run(process: BaseAzadProcess, name: str = None):
        with boundedSemaphore:
            if not name:
                logger.debug("Starting process object %s..", process)
            else:
                logger.debug("Starting process '%s'..", name)
            process.start()
            process.join()
            if not name:
                logger.debug("Finishing process object %s..", process)
            else:
                logger.debug("Finishing process '%s'..", name)

    # Make threads and run
    totalThreadCount = len(processes)
    logTTC = 1
    while 10 ** logTTC < totalThreadCount:
        logTTC += 1
    getName = (lambda i: None if processNamePrefix is None
               else processNamePrefix + ("_%%0%dd" % (logTTC,) % (i,)))
    threads = [threading.Thread(target=run, args=(processes[i],),
                                kwargs={"name": getName(i + 1)})
               for i in range(totalThreadCount)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    pass
