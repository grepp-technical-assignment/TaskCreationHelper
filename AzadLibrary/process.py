"""
This module provides advanced multiprocessing functionalities.
"""

# Standard libraries
from math import inf
import typing
from pathlib import Path
import time
import os
from threading import Thread
import multiprocessing
import json
import traceback

# Azad libraries
from .errors import AzadTLE
from .constants import (
    SourceFileType,
    ExitCodeSuccess, ExitCodeFailGeneral,
    ExitCodeTLE, ExitCodeMLE,
    ExitCodeFailedToReturnData, ExitCodeFailedInAVPhase,
)
from .externalmodule import prepareExecFunc
from .misc import randomName
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

    def __init__(self, *args__, timelimit: float = None,
                 outFilePath: typing.Union[Path, str] = None,
                 **kwargs__):
        """
        If `timelimit` is given, then the process will automatically terminates after execution.
        If `outFilePath` is given, then the result will be outputted into file with json/traceback format.
            Give this argument only if when your function returns primitive type only.
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

        # Json Outfile
        self.outFilePath = Path(outFilePath) if outFilePath else None
        if self.outFilePath and self.outFilePath.exists():
            raise OSError("Target file '%s' already exists" %
                          (self.outFilePath,))

        # Misc
        self.outfileCleaned = False
        self.returnedValue = None
        self.raisedTraceback = None

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

    def internalPhaseLoop(self):
        """
        This is one of execution phases.
        In this phase, process executes target function under TLE.
        """
        self.capsuleResult = None
        self.capsuleException: BaseException = None
        mainThread = Thread(
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
                        json.dump(self.capsuleResult, outFile)
                    else:
                        assert isinstance(self.capsuleException, BaseException)
                        traceback.print_exception(
                            type(self.capsuleException),
                            self.capsuleException,
                            self.capsuleException.__traceback__,
                            file=outFile)
        except BaseException:  # Failed to return data
            exit(ExitCodeFailedToReturnData)

    def limitRAM(self, newsoft: int):
        """
        Limit ram of created process.
        """
        import resource
        oldsoft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (newsoft, hard))

    def run(self):
        """
        Actual execution process.
        Function return result will be `self.capsuleResult`.
        Raised exception will be `self.capsuleException`.
        """
        self.limitRAM(1024 << 20)  # Resource limitation
        self.internalPhaseLoop()  # Looping phase; TLE will exit here
        try:
            self.internalPhaseAfterValidation()
        except BaseException as err:  # Failed after-validation phase
            self.capsuleException = err
            self.internalPhaseWriteOutFile()
            exit(ExitCodeFailedInAVPhase)
        else:
            self.internalPhaseWriteOutFile()
            if self.capsuleException:  # General execution failure
                exit(ExitCodeFailGeneral)
            else:  # Successful termination
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
        with open(self.outFilePath, "r") as outFile:
            if self.exitcode == ExitCodeSuccess:
                self.returnedValue = json.load(outFile)
            else:
                self.raisedTraceback = outFile.read()
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

    def close(self):
        super().close()
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
                 sourceFileType: SourceFileType,
                 *args__, timelimit: float = None, **kwargs__):
        """
        You should not give `target` as parameter.
        You should give `timelimit` as parameter,
        because external module function should have time limit to execute.
        """

        if "target" in kwargs__ and kwargs__["target"] is not None:
            raise ValueError("target should be None.")
        elif timelimit is None:
            raise ValueError("timelimit should be specified.")
        super().__init__(*args__, target=None, timelimit=timelimit, **kwargs__)
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
            except BaseException as err:
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
            self, sourceFilePath: typing.Union[str, Path], *args__, **kwargs__):
        super().__init__(
            sourceFilePath, SourceFileType.Validator, *args__, **kwargs__)


class AzadProcessSolution(AzadProcessForModules):
    """
    AzadProcess used for solutions.
    """

    def __init__(
            self, sourceFilePath: typing.Union[str, Path],
            returnValueInfo: dict, *args__,
            outFilePath: typing.Union[str, Path] = None, **kwargs__):
        """
        For `returnValueInfo`, give `AzadCore.returnValueInfo`.
        For `outFilePath`, if not given, then process will generate random name.
        """
        if outFilePath is None:
            outFilePath = "solution_process_" + randomName(64) + ".temp"
        super().__init__(
            sourceFilePath, SourceFileType.Solution,
            outFilePath=outFilePath, *args__, **kwargs__)

        # Return value info
        self.returnValueInfo = returnValueInfo

    def internalPhaseAfterValidation(self):
        """
        Validate if generated result is fit for target return value.
        """
        assert checkDataType(
            self.capsuleResult, self.returnValueInfo["type"],
            self.returnValueInfo["dimension"])
        assert checkDataCompatibility(
            self.capsuleResult, self.returnValueInfo["type"])

    def internalPhaseWriteOutFile(self):
        return super().internalPhaseWriteOutFile()


if __name__ == "__main__":
    pass
