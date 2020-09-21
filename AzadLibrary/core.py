"""
This module is core of Azad library.
"""

# Standard libraries
import json
import os
from pathlib import Path
import typing
import time
import atexit
import gc
import logging
import warnings
import threading

logger = logging.getLogger(__name__)

# Azad libraries
from . import (
    constants as Const, errors as Errors,
    externalmodule as ExternalModule,
    iodata as IOData,
)
from .misc import (validateVerdict, getAvailableCPUCount, getExtension)
from .filesystem import TempFileSystem
from .configparse import TaskConfiguration


class AzadCore:
    """
    Azad library's core object generated from config.json
    """

    def __init__(self, configFilename: typing.Union[str, Path],
                 resetRootLoggerConfig: bool = True):

        logger.info("Azad Library Version is %s", Const.AzadLibraryVersion)
        logger.info("Current directory is %s", os.getcwd())

        # Upper bound of number of threads
        CPUcount = getAvailableCPUCount()
        self.threadUpperBound: int = CPUcount if CPUcount is not None else 1
        logger.info("Total %s processor cores are available.",
                    CPUcount if CPUcount else "unknown")

        # Get configuration JSON
        if not isinstance(configFilename, (str, Path)):
            raise TypeError
        elif isinstance(configFilename, str):
            configFilename = Path(configFilename)
        with open(configFilename, "r") as configFile:
            parsedConfig: dict = json.load(configFile)
        self.config = TaskConfiguration(
            configFilename.parent,
            resetRootLoggerConfig=resetRootLoggerConfig,
            **parsedConfig)

        # Module attributes
        self.generatorModules: typing.Mapping[
            str, ExternalModule.AbstractExternalGenerator] = {}  # {name: module}
        self.validatorModule: typing.Union[
            ExternalModule.AbstractExternalValidator, None] = None
        self.solutionModules: typing.Mapping[
            typing.Tuple[Const.IOVariableTypes, ...],
            typing.List[ExternalModule.AbstractExternalSolution]
        ] = {}  # {(category, ...): [module, ...]}

        # Inner attributes and flags
        self.producedAnswers = []
        self.inputDatas = []

        # File system
        self.fs = TempFileSystem(self.config.directory)

        # Reserve termination
        atexit.register(self.terminate)

    def terminate(self):
        """
        Terminate.
        """
        logger.info("Terminating Azad core..")
        del self.producedAnswers
        del self.inputDatas

    def prepareModules(self):
        """
        Prepare all modules for ready to invoke.
        """
        logger.info("Preparing modules..")

        def getModule(
                modulePath: Path, filetype: Const.SourceFileType,
                name: str) -> ExternalModule.AbstractExternalModule:
            """
            Helper function for getting module.
            """
            extension = getExtension(modulePath)
            lang = Const.getSourceFileLanguage(extension)
            return ExternalModule.getExternalModuleClass(lang, filetype)(
                modulePath, self.fs, self.config.parameters,
                (self.config.returnType, self.config.returnDimension),
                name=name)

        # Generator modules
        for generatorName in self.config.generators:
            self.generatorModules[generatorName] = getModule(
                self.config.generators[generatorName],
                Const.SourceFileType.Generator,
                "Generator %s" % (generatorName,))

        # Validator module
        if self.config.validator:
            self.validatorModule = getModule(
                self.config.validator,
                Const.SourceFileType.Validator, "Validator")

        # Solution modules
        for categories in self.config.solutions:
            for path in self.config.solutions[categories]:
                self.solutionModules = getModule(
                    path, Const.SourceFileType.Solution,
                    "Solution '%s'" % (path.name,))

    def generateInput(self) -> typing.List[Path]:
        """
        Generate all input data as file and return those files.
        If there is an error in any generation process, raise an error.
        """
        if not self.config.genscripts:
            raise ValueError("There is no genscript")
        logger.info("Generating input data..")

        # Prepare stuffs
        semaphore = threading.BoundedSemaphore(self.threadUpperBound)
        results: typing.List[Const.EXOO] = \
            [(None, None, None) for _ in self.config.genscripts]

        def run(index: int):
            """
            Helper function to run independent generator subprocess.
            Use this under multithreading.
            """
            with semaphore:
                logger.debug("Starting generation #%d..", index + 1)
                genscript = self.config.genscripts[index]
                generatorName = genscript[0]
                module = self.generatorModules[generatorName]
                startTime = time.perf_counter()
                results[index] = module.run(genscript)
                endTime = time.perf_counter()
                logger.debug("Finishing generation #%d in %gs..",
                             index + 1, endTime - startTime)

        # Do multiprocessing
        threads = [threading.Thread(target=run, args=(i,))
                   for i in range(len(self.config.genscripts))]
        startTime = time.perf_counter()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        endTime = time.perf_counter()
        logger.info("Finished all generator process in %g seconds.",
                    endTime - startTime)

        # Check if there is any failure
        failedIndices = []
        for i in range(len(results)):
            exitcode, inputDataPath, errLog = results[i]
            if exitcode is not Const.ExitCode.Success:  # Failed
                failedIndices.append(i)
                with open(errLog, "r") as errorLogFile:
                    logger.error(
                        "Generation #%d failed(%s, genscript = '%s'); Error log:\n%s",
                        i + 1, exitcode.name, self.config.genscripts[i],
                        errorLogFile.read())
            else:  # Even if exit code is success, try parsing
                try:
                    with open(inputDataPath, "r") as inputFile:
                        iterator = IOData.yieldLines(inputFile)
                        for _0, iovt, dimension in self.config.parameters:
                            IOData.parseMulti(iterator, iovt, dimension)
                except (StopIteration, TypeError, ValueError) as err:
                    logger.error("Error raised while parsing input data #%d (genscript = '%s')",
                                 i + 1, self.config.genscripts[i])
                    raise err.with_traceback(err.__traceback__)

        # Finalize
        if failedIndices:
            raise Errors.FailedDataGeneration(
                "Generator process failed on %s; Please check log file" %
                ("".join("#%d" % (i + 1,) for i in failedIndices),))
        else:  # Successfully generated
            for _0, _1, errLog in results:
                self.fs.pop(errLog)
            gc.collect()
            return [inputDataPath for (_0, inputDataPath, _2) in results]

    def validateInput(self, inputFiles: typing.List[Path]):
        """
        Validate all data from input files generated by generators.
        """
        if self.validatorModule is None:  # If there isn't module just go
            warnings.warn("There is no validator")
            return

        # Prepare stuffs
        semaphore = threading.BoundedSemaphore(self.threadUpperBound)
        results: typing.List[Const.EXOO] = \
            [(None, None, None) for _ in inputFiles]

        def run(index: int):
            """
            Helper function to run independent validator subprocess.
            Use this under multithreading.
            """
            with semaphore:
                logger.debug("Starting validation #%d..", index + 1)
                startTime = time.perf_counter()
                results[index] = self.validatorModule.run(inputFiles[index])
                endTime = time.perf_counter()
                logger.debug("Finishing validation #%d in %gs..",
                             index + 1, endTime - startTime)

        # Do multithreading
        threads = [threading.Thread(target=run, args=(i,))
                   for i in range(len(inputFiles))]
        startTime = time.perf_counter()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        endTime = time.perf_counter()
        logger.info("Finished all validation process in %g seconds",
                    endTime - startTime)

        # Check if there is any failure
        failedIndices = []
        for i in range(len(results)):
            exitcode, _, errLog = results[i]
            if exitcode is not Const.ExitCode.Success:
                failedIndices.append(i)
                with open(errLog, "r") as errorLogFile:
                    logger.error(
                        "Validation #%d failed(%s); Error log:\n%s",
                        i + 1, exitcode.name, errorLogFile.read())
        if failedIndices:
            raise Errors.FailedDataValidation(
                "Validation process failed on %s; Please check log file" %
                ("".join("#%d" % (i + 1,) for i in failedIndices),))
        else:
            for _0, _1, errLog in results:
                self.fs.pop(errLog)
            gc.collect()

    def generateOutput(
            self, module: ExternalModule.AbstractExternalSolution,
            inputFiles: typing.List[Path],
            intendedCategories: typing.Tuple[Const.Verdict, ...],
            compare: bool = True, answers: typing.List[typing.Any] = (),
            solutionName: str = "Unknown") -> typing.List[Path]:
        """
        Generate output files with given solution module and input files.
        If `compare` flag is True, then it compares result
        against given `answerFiles` and determine AC/WA.
        """
        if not inputFiles:
            raise ValueError("No input files given")
        elif compare and len(inputFiles) != len(answers):
            raise ValueError("Different length of provided file lists")

        # Prepare stuffs
        logger.info("Starting solution '%s'..", solutionName)
        result: typing.List[Const.EXOO] = \
            [(None, None, None) for _ in inputFiles]
        semaphore = threading.BoundedSemaphore(self.threadUpperBound)

        def run(index: int):
            """
            Helper function to run independent validator subprocess.
            Use this under multithreading.
            """
            with semaphore:
                logger.debug("Starting solution '%s' #%d..",
                             solutionName, index + 1)
                startTime = time.perf_counter()
                result[index] = module.run(
                    inputFiles[index], timelimit=self.config.TL)
                endTime = time.perf_counter()
                logger.debug("Finishing solution '%s' #%d in %gs..",
                             solutionName, index + 1, endTime - startTime)

        # Do multithreading
        threads = [threading.Thread(target=run, args=(i,))
                   for i in range(len(inputFiles))]
        startTime = time.perf_counter()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        endTime = time.perf_counter()
        logger.info("Finished all solution '%s' process in %g seconds.",
                    solutionName, endTime - startTime)

        # Determine verdicts
        logger.debug("Analyzing verdicts of solution '%s' (intended %s)..",
                     solutionName, ", ".join(c.name for c in intendedCategories))
        verdicts: typing.List[Const.Verdict] = []
        for i in range(len(inputFiles)):
            exitcode, _1, _2 = result[i]
            verdict = Const.Verdict.FAIL
            if exitcode is Const.ExitCode.Success:
                if not compare:
                    verdict = Const.Verdict.AC
                else:
                    raise NotImplementedError
            elif exitcode is Const.ExitCode.TLE:
                verdict = Const.Verdict.TLE
            elif exitcode is Const.ExitCode.MLE:
                verdict = Const.Verdict.MLE
            verdicts.append(verdict)

        # Analyze verdicts
        logger.debug("Verdicts: [%s]", ", ".join(
            "%s" % (v.name,) if v is not Const.Verdict.FAIL
            else "%s(%s)" % (v.name, r[0].name)
            for v, r in zip(verdicts, result)))
        verdictCount = {verdict: verdicts.count(verdict)
                        for verdict in Const.Verdict}
        if not validateVerdict(verdictCount, *intendedCategories):
            for i in range(len(inputFiles)):
                verdict = verdicts[i]
                if verdict is not Const.Verdict.AC and \
                        verdict not in intendedCategories:
                    with open(result[i][2], "r") as errLogFile:
                        errLogContent = errLogFile.read()
                    logger.error(
                        "Solution '%s' produced wrong verdict %s on test #%d; Report: \n%s",
                        solutionName, verdict, i + 1, errLogContent)
                    del errLogContent
            raise Errors.WrongSolutionFileCategory(
                "Solution '%s' does not worked as intended(%s)." %
                (solutionName, ",".join(str(s) for s in intendedCategories)))
        else:  # Success, now let's remove error log.
            for _0, _1, errLog in result:
                self.fs.pop(errLog)
            gc.collect()
            return [outfilePath for (_0, outfilePath, _2) in result]

    def generateOutputs(self, inputFiles: typing.List[Path],
                        mainACOnly: bool = True) -> list:
        """
        Execute and validate each solutions.
        """
        if not inputFiles:
            raise ValueError("No input files given")

        # Run main AC first
        AConly: typing.Tuple[Const.Verdict, ...] = (Const.Verdict.AC,)
        mainACModule: ExternalModule.AbstractExternalSolution = \
            self.solutionModules[AConly][0]
        answerFiles: typing.List[Path] = self.generateOutput(
            mainACModule, inputFiles, AConly, compare=False,
            solutionName="MAIN (%s)" % (self.config.solutions[AConly][0],))

        # Constraint validation
        answers = []
        for i in range(len(answerFiles)):
            answerFile = answerFiles[i]
            iterator = IOData.yieldLines(answerFile)
            try:
                answers.append(
                    IOData.parseMulti(iterator, self.config.returnType,
                                      self.config.returnDimension))
                self.fs.pop(answerFile)
            except ValueError as err:
                logger.error("Main solution produced wrong data on #%d", i + 1)
                raise err.with_traceback(err.__traceback__)
        del answerFiles

        # Run all other solution files
        if not mainACOnly:
            for category in self.solutionModules:
                for i in range(list(self.solutionModules[category])):
                    module = self.solutionModules[category][i]
                    if module is mainACModule:
                        continue
                    result = self.generateOutput(
                        module, inputFiles, category, answers=answers,
                        solutionName=str(self.config.solutions[category][i]))
                    for outfilePath in result:  # Also remove outfiles
                        self.fs.pop(outfilePath)
                    gc.collect()

        # Return answer files
        gc.collect()
        return answers

    def writePGInFiles(self, inFiles: typing.List[Path]):
        """
        Read and convert parameters info PGized form into `self.config.IOPath`.
        """
        logger.info("Writing PGized input files..")
        for i in range(len(inFiles)):
            outPath = self.config.IOPath / \
                (self.config.inputFilePathSyntax % (i + 1,))
            logger.debug("Writing '%s'..", outPath)
            with open(inFiles[i], "r") as inputFile:
                iterator = IOData.yieldLines(inputFile)
                data = [IOData.parseMulti(iterator, paramType, dimension)
                        for (_0, paramType, dimension) in self.config.parameters]
                with open(outPath, "w") as outFile:
                    outFile.write(",".join(
                        IOData.PGizeData(e, t)
                        for e, (_0, t, _2) in zip(data, self.config.parameters)))

    def writePGOutFiles(self, answers: list):
        """
        Convert answers into PGized form into `self.config.IOPath`.
        """
        logger.info("Writing PGized output files..")
        for i in range(len(answers)):
            outPath = self.config.IOPath / \
                (self.config.outputFilePathSyntax % (i + 1,))
            logger.debug("Writing '%s'..", outPath)
            with open(outPath, "w") as outFile:
                outFile.write(IOData.PGizeData(
                    answers[i], self.config.returnType))

    def totalPipeline(self, mode: Const.AzadLibraryMode):
        """
        Execute total pipeline with given mode.
        """
        if not isinstance(mode, Const.AzadLibraryMode):
            raise TypeError("Invalid mode type %s" % (type(mode),))

        # Generate external codes
        self.prepareModules()
        if mode is Const.AzadLibraryMode.GenerateCode:
            while True:
                line = input("When you are ready, enter 'Q' to quit:")
                if line.strip().upper() == 'Q':
                    break
            return

        # Go full or produce?
        inputDataFiles = self.generateInput()
        self.validateInput(inputDataFiles)
        answers = self.generateOutputs(
            inputDataFiles, mainACOnly=(mode is Const.AzadLibraryMode.Full))

        # Write PGized I/O files
        IOData.cleanIOFilePath(self.config.IOPath)
        self.writePGInFiles(inputDataFiles)
        self.writePGOutFiles(answers)
        for file in inputDataFiles:
            self.fs.pop(file)
