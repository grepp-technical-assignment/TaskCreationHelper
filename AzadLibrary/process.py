"""
This module provides advanced multiprocessing functionalities.
"""

# Standard libraries
from math import inf
import typing
from pathlib import Path
import time
import os
import sys
from threading import Thread
import multiprocessing
import json

# Azad libraries
from .errors import AzadTLE
from .constants import (
    SourceFileType,
    ExitCodeSuccess, ExitCodeFailedBase,
    ExitCodeTLE, ExitCodeMLE, ExitCodeFATAL,
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
                 jsonOutFilePath: typing.Union[Path, str] = None,
                 **kwargs__):
        """
        If `timelimit` is given, then the process will automatically terminates after execution.
        If `jsonOutFile` is given, then the result will be outputted into jsonOutFile with json format.
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
        self.jsonOutFilePath = Path(jsonOutFilePath) \
            if jsonOutFilePath else None
        if self.jsonOutFilePath and self.jsonOutFilePath.exists():
            raise OSError("Target file '%s' already exists" %
                          (self.jsonOutFilePath,))

        # Misc
        self.outfileCleaned = False
        self.returnedValue = None

    def getCapsule(self):
        """
        Get capsulized function to execute in loop phase.
        This method can be overrided in subclasses.
        """
        def func(*args, **kwargs):
            nonlocal self
            self.capsuleResult = self._target(*self._args, **self._kwargs)
        return func

    def _loopPhase(self):
        """
        Loop phase of execution.
        This phase determines TLE or not.
        """
        self.capsuleResult = None
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
        except AzadTLE:
            exit(ExitCodeTLE)
        except BaseException:
            exit(ExitCodeFATAL)

    def run(self):
        """
        Actual execution process.
        Function return result will be `self.capsuleResult`.
        """
        self._loopPhase()
        try:
            if self.jsonOutFilePath:
                with open(self.jsonOutFilePath, "w") as outFile:
                    json.dump(self.capsuleResult, outFile)
        except BaseException:
            exit(ExitCodeFailedToReturnData)
        else:
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
            if self.jsonOutFilePath.exists() and self.jsonOutFilePath.is_file():
                with open(self.jsonOutFilePath, "r") as jsonFile:
                    self.returnedValue = json.load(jsonFile)
        try:
            os.remove(self.jsonOutFilePath)
        except FileNotFoundError:
            pass

        # Mark as cleaned
        self.outfileCleaned = True

    def join(self):
        super().join()
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
    """

    def __init__(self,
                 sourceFilePath: typing.Union[str, Path],
                 sourceFileType: SourceFileType,
                 *args__,
                 jsonOutFilePath: typing.Union[Path, str] = None,
                 **kwargs__):
        """
        You shouldn't give `target` as parameter.
        """

        if "target" in kwargs__ and kwargs__["target"] is not None:
            raise ValueError("target should be None")
        elif jsonOutFilePath is None:
            jsonOutFilePath = "module_" + randomName(64) + ".json"
        super().__init__(*args__, target=None,
                         jsonOutFilePath=jsonOutFilePath,
                         **kwargs__)
        self.sourceFilePath = Path(sourceFilePath)
        self.sourceFileType = sourceFileType

    def getCapsule(self):
        """
        Generate and call module function instead of just calling `self._target`.
        """

        moduleFunc = prepareExecFunc(self.sourceFilePath, self.sourceFileType)

        def func(*args, **kwargs):
            nonlocal self, moduleFunc
            self.capsuleResult = moduleFunc(*self._args, **self._kwargs)
        return func


class AzadProcessGenerator(AzadProcessForModules):
    """
    AzadProcess used for generators.
    """

    def getCapsule(self):
        target = super().getCapsule()

        def func(args: typing.List[str]):
            nonlocal self, target
            import random
            import hashlib
            hashValue = hashlib.sha256("|".join(args).encode()).hexdigest()
            random.seed(hashValue)
            self.capsuleResult = target(args)
        return func


class AzadProcessValidator(AzadProcessForModules):
    """
    AzadProcess used for validators.
    Be aware that `AssertionError` is the only allowed exception during validation.
    """

    def getCapsule(self):
        target = super().getCapsule()

        def func(*args, **kwargs):
            nonlocal self, target
            try:
                target(*args, **kwargs)
            except AssertionError as err:
                self.capsuleResult = False
            else:
                self.capsuleResult = True
        return func


class AzadProcessSolution(AzadProcessForModules):
    """
    AzadProcess used for solutions.
    """

    def getCapsule(self):
        target = super().getCapsule()

        def func(*args, **kwargs):
            nonlocal self, target
            self.capsuleResult = target(*args, **kwargs)
        return func


if __name__ == "__main__":
    pass
