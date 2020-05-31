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
    ExitCodeFailedToReturnData,
)
from .externalmodule import prepareExecFunc
from .misc import randomName

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
        """
        def func(*args, **kwargs):
            nonlocal self
            try:
                self.capsuleResult = self._target(*self._args, **self._kwargs)
            except BaseException as err:
                self.capsuleException = err
        return func

    def run(self):
        """
        Actual execution process.
        Function return result will be `self.capsuleResult`.
        """
        self.capsuleResult = None
        self.capsuleException = None
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
                    # Successfully terminated
                    break
                else:
                    time.sleep(self.minDT)
        except AzadTLE:  # TLE
            exit(ExitCodeTLE)
        else:  # Thread terminated
            try:
                if self.outFilePath:
                    with open(self.outFilePath, "w") as outFile:
                        if self.capsuleException is None:
                            json.dump(self.capsuleResult, outFile)
                        else:
                            traceback.print_exception(
                                type(self.capsuleException),
                                self.capsuleException,
                                self.capsuleException.__traceback__,
                                file=outFile)
            except BaseException:  # Failed to return data
                exit(ExitCodeFailedToReturnData)
            else:
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

        # Json Outfile
        if self.exitcode == ExitCodeSuccess:
            if self.outFilePath.exists() and self.outFilePath.is_file():
                with open(self.outFilePath, "r") as jsonFile:
                    self.returnedValue = json.load(jsonFile)
        elif self.exitcode == ExitCodeFailGeneral:
            if self.outFilePath.exists() and self.outFilePath.is_file():
                with open(self.outFilePath, "r") as excFile:
                    self.raisedTraceback = excFile.read()
        try:
            os.remove(self.outFilePath)
        except FileNotFoundError:
            pass

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
    AzadProcess used for general modules.
    Since we can't send non-global function to spawned process (unpicklable),
    we take function which generates real function from module instead,
    and replace target by that real function.

    The reason why I ensure `outFilePath` exists (even though validators
    doesn't need any return unless we change implementation) is consistency.
    """

    def __init__(self,
                 sourceFilePath: typing.Union[str, Path],
                 sourceFileType: SourceFileType,
                 *args__,
                 outFilePath: typing.Union[Path, str] = None,
                 timelimit: float = None,
                 **kwargs__):
        """
        You should not give `target` as parameter.
        You should give `timelimit` as parameter,
        because external module function should have time limit to execute.
        """

        if "target" in kwargs__ and kwargs__["target"] is not None:
            raise ValueError("target should be None.")
        elif timelimit is None:
            raise ValueError("timelimit should be specified.")
        if outFilePath is None:
            outFilePath = "module_" + randomName(64) + ".json"
        super().__init__(*args__, target=None, timelimit=timelimit,
                         outFilePath=outFilePath, **kwargs__)
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
                 args: typing.List[str], *args__, **kwargs__):
        """
        Just give list of strings to `args`.
        It will be automatically converted.
        """
        super().__init__(
            sourceFilePath, SourceFileType.Generator,
            *args__, args=[args], **kwargs__)

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


class AzadProcessValidator(AzadProcessForModules):
    """
    AzadProcess used for validators.
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
            self, sourceFilePath: typing.Union[str, Path], *args__, **kwargs__):
        super().__init__(
            sourceFilePath, SourceFileType.Solution, *args__, **kwargs__)


if __name__ == "__main__":
    pass
