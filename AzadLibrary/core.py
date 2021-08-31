"""
This module is core of Azad library.
"""

# Standard libraries
import json
import os
from pathlib import Path
import typing
import atexit
import gc
import logging
import warnings
import uuid

logger = logging.getLogger(__name__)

# Azad libraries
from . import (
    constants as Const, errors as Errors,
    externalmodule as ExternalModule,
    iodata as IOData,
)
from .misc import (
    validateVerdict, getAvailableTasksCount,
    getExtension, runThreads, pause,
    formatPathForLog, reportSolutionStatistics)
from .filesystem import TempFileSystem
from .configparse import TaskConfiguration


class AzadCore:
    """
    Azad library's core object generated from config.json
    """

    def __init__(self, configFilename: typing.Union[str, Path],
                 resetRootLoggerConfig: bool = True,
                 logLevel: int = logging.NOTSET):

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
            logLevel=logLevel,
            **parsedConfig)

        # Let's go
        logger.info("Azad Library Version is %s", Const.AzadLibraryVersion)
        logger.info("Current directory is %s",
                    formatPathForLog(Path(os.getcwd())))

        # Upper bound of number of threads
        self.concurrencyCount = getAvailableTasksCount()
        logger.info("Total %d concurrent tasks will run.",
                    self.concurrencyCount)

        # Replace precision equality function
        _iovt_precision_eq = (
            lambda x, y: Const.checkPrecision(
                x, y, precision=self.config.floatPrecision))
        Const.IODataTypesInfo[Const.IOVariableTypes.FLOAT]["equal"] = \
            _iovt_precision_eq
        Const.IODataTypesInfo[Const.IOVariableTypes.DOUBLE]["equal"] = \
            _iovt_precision_eq

        # Module attributes
        self.generatorModules: typing.Mapping[
            str, ExternalModule.AbstractExternalGenerator] = {}  # {name: module}
        self.validatorModule: typing.Union[
            ExternalModule.AbstractExternalValidator, None] = None
        self.solutionModules: typing.Mapping[
            typing.Tuple[Const.IOVariableTypes, ...],
            typing.List[ExternalModule.AbstractExternalSolution]
        ] = {}  # {(category, ...): [module, ...]}
        self.solutionModulesByPath: typing.Mapping[
            Path, ExternalModule.AbstractExternalSolution] = {}

        # Inner attributes and flags
        self.producedAnswers = []
        self.inputDatas = []

        # File system
        self.fs = TempFileSystem(self.config.directory / "__TCH_TFS")

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

        # Language specification for kwargs in getModule function
        # The reason why I put this here instead of function interface is,
        # because these values are dynamic(unpredictable).
        _kwargs_lang_specification = {
            Const.SourceFileLanguage.Python3: {
                "ioHelperModulePath":
                ExternalModule.AbstractPython3.ioHelperTemplatePath
            }
        }

        def getModule(sourceCodePath: Path, filetype: Const.SourceFileType,
                      name: str) -> ExternalModule.AbstractExternalModule:
            """
            Helper function for getting module.
            """
            # Basics
            extension = getExtension(sourceCodePath)
            lang = Const.getSourceFileLanguage(extension)
            moduleFolder = self.fs.newFolder(namePrefix=filetype.name)

            # Prepare type, args and kwargs
            moduleType = ExternalModule.getExternalModuleClass(lang, filetype)
            args = (self.fs, moduleFolder, self.config.parameters,
                    (self.config.returnType, self.config.returnDimension),
                    sourceCodePath)
            kwargs = {"name": name}
            if lang in _kwargs_lang_specification:
                kwargs.update(_kwargs_lang_specification[lang])

            # Return
            return moduleType(*args, **kwargs)

        # Generator modules
        for generatorName in self.config.generators:
            self.generatorModules[generatorName] = getModule(
                self.config.generators[generatorName],
                Const.SourceFileType.Generator,
                "Generator %s" % (generatorName,))
            self.generatorModules[generatorName].preparePipeline()
            logger.debug("Prepared generator \"%s\".", generatorName)

        # Validator module
        if self.config.validator:
            self.validatorModule = getModule(
                self.config.validator,
                Const.SourceFileType.Validator, "Validator")
            self.validatorModule.preparePipeline()
            logger.debug("Prepared validator.")

        # Solution modules
        for categories in self.config.solutions:
            self.solutionModules[categories] = []
            for path in self.config.solutions[categories]:
                module = getModule(
                    path, Const.SourceFileType.Solution,
                    "Solution '%s'" % (formatPathForLog(path),))
                self.solutionModules[categories].append(module)
                self.solutionModulesByPath[path] = module
                self.solutionModules[categories][-1].preparePipeline()
                logger.debug("Prepared solution \"%s\".",
                             formatPathForLog(path))

    def runGeneration(self, genscript: typing.List[str]) -> Const.EXOO:
        generatorName = genscript[0]
        module = self.generatorModules[generatorName]
        result = module.run(genscript[1:])
        return result

    def generateInput(
            self, genscripts: typing.List[typing.List[str]]) -> typing.List[Path]:
        """
        Generate all input data as file and return those files.
        If there is an error in any generation process, raise an error.
        """
        if not genscripts:
            raise ValueError("There is no genscript")
        logger.info("Generating input data..")

        # Prepare stuffs
        results: typing.List[Const.EXOO] = \
            [(None, None, None) for _ in genscripts]

        def run(index: int):
            """
            Helper function to run independent generator subprocess.
            Use this under `misc.runThreads`.
            """
            results[index] = self.runGeneration(genscripts[index])

        # Do multiprocessing
        timeDiff, dtDistribution = runThreads(
            run, self.concurrencyCount,
            *[((i,), {}) for i in range(len(genscripts))],
            funcName="Generation")
        logger.info("Finished all generation in %g seconds.", timeDiff)
        logger.debug("DT: [%s]", ", ".join(
            "%g" % dt for dt in dtDistribution))

        # Check if there is any failure
        failedIndices = []
        logger.info("Parsing all data..")
        for i in range(len(results)):
            exitcode, inputDataPath, errLog = results[i]
            if exitcode is not Const.ExitCode.Success:  # Failed
                failedIndices.append(i)
                with open(errLog, "r") as errorLogFile:
                    logger.error(
                        "Generation #%d failed(%s, genscript = \"%s\"); Error log:\n%s",
                        i + 1, exitcode.name, genscripts[i],
                        errorLogFile.read())
            else:  # Even if exit code is success, try parsing
                try:
                    logger.debug("Parsing data #%d..", i + 1)
                    iterator = IOData.yieldLines(inputDataPath)
                    for varName, iovt, dimension in self.config.parameters:
                        logger.debug(
                            "Parsing data #%d: parameter '%s'..", i + 1, varName)
                        IOData.parseMulti(iterator, iovt, dimension)
                    del iterator
                    gc.collect()
                except (StopIteration, TypeError, ValueError) as err:
                    logger.error("Error raised while parsing input data #%d (genscript = \"%s\")",
                                 i + 1, genscripts[i])
                    raise err.with_traceback(err.__traceback__)

        # Finalize
        if failedIndices:
            raise Errors.FailedDataGeneration(
                "Generator process failed on %s; Please check log file" %
                (", ".join("#%d" % (i + 1,) for i in failedIndices),))
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
        logger.info("Validating input..")
        results: typing.List[Const.EXOO] = \
            [(None, None, None) for _ in inputFiles]

        def run(index: int):
            """
            Helper function to run independent validator subprocess.
            Use this under multithreading.
            """
            results[index] = self.validatorModule.run(inputFiles[index])

        # Do multithreading
        timeDiff, _ = runThreads(
            run, self.concurrencyCount,
            *[((i,), {}) for i in range(len(inputFiles))],
            funcName="Validation")
        logger.info("Finished all validation in %g seconds.", timeDiff)

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
                (", ".join("#%d" % (i + 1,) for i in failedIndices),))
        else:
            for _0, _1, errLog in results:
                self.fs.pop(errLog)
            gc.collect()

    def generateOutput(
        self, module: ExternalModule.AbstractExternalSolution,
        inputFiles: typing.List[Path],
        intendedCategories: typing.Tuple[Const.Verdict, ...],
        compare: bool = True, returnVerdicts: bool = False,
        answers: typing.List[typing.Any] = (),
        solutionName: str = "Unknown",
        TL: float = None, ML: float = None) \
            -> typing.Union[typing.List[Path], typing.List[Const.Verdict]]:
        """
        Generate output files with given solution module and input files.
        If `compare` flag is True, then it compares result
        against given `answers` and determine AC/WA.
        If `raiseOnInvalidVerdict` is False, then return verdicts instead of raising errors.
        """
        if not inputFiles:
            raise ValueError("No input files given")
        elif compare and len(inputFiles) != len(answers):
            raise ValueError("Different length of provided file lists")

        # Prepare stuffs
        logger.info("Starting solution \"%s\"..", solutionName)
        result: typing.List[Const.EXOO] = \
            [(None, None, None) for _ in inputFiles]

        def run(index: int):
            """
            Helper function to run independent validator subprocess.
            Use this under multithreading.
            """
            result[index] = module.run(
                inputFiles[index],
                timelimit=self.config.TL if TL is None else TL,
                memorylimit=self.config.ML if ML is None else ML)

        # Do multithreading
        timeDiff, dtDistribution = runThreads(
            run, self.concurrencyCount,
            *[((i,), {}) for i in range(len(inputFiles))],
            funcName="Solution '%s'" % (solutionName,))
        logger.info("Finished solution \"%s\" in %g seconds.",
                    solutionName, timeDiff)

        # Determine verdicts
        logger.debug("Analyzing verdicts (intended %s)..",
                     ", ".join(c.name for c in intendedCategories))
        verdicts: typing.List[Const.Verdict] = []
        for i in range(len(inputFiles)):
            exitcode, outfilePath, _2 = result[i]
            verdict = Const.Verdict.FAIL
            if exitcode is Const.ExitCode.Success:  # AC/WA
                if not compare:
                    verdict = Const.Verdict.AC
                else:
                    answer = answers[i]
                    produced = IOData.parseMulti(
                        IOData.yieldLines(outfilePath),
                        self.config.returnType,
                        self.config.returnDimension)
                    verdict = Const.Verdict.AC if IOData.isCorrectAnswer(
                        answer, produced,
                        self.config.returnType,
                        self.config.returnDimension) \
                        else Const.Verdict.WA
            elif exitcode is Const.ExitCode.TLE:
                verdict = Const.Verdict.TLE
            elif exitcode is Const.ExitCode.MLE:
                verdict = Const.Verdict.MLE
            verdicts.append(verdict)

        # Report and analyze verdicts
        reportSolutionStatistics(verdicts, dtDistribution)
        verdictCount = {verdict: verdicts.count(verdict)
                        for verdict in Const.Verdict}

        # Should return verdicts
        if returnVerdicts:
            for _0, outFile, errLog in result:
                self.fs.pop(outFile)
                self.fs.pop(errLog)
            return verdicts

        # What if verdict is wrong? Raise an error instead.
        elif not validateVerdict(verdictCount, *intendedCategories):

            # Report for all wrong verdict indices
            for i in range(len(inputFiles)):
                verdict = verdicts[i]
                if verdict is not Const.Verdict.AC and \
                        verdict not in intendedCategories:

                    # Print error log
                    with open(result[i][1] if verdict is Const.Verdict.WA
                              else result[i][2], "r",
                              encoding="ascii" if verdict is Const.Verdict.WA
                              else "utf-8") as errLogFile:
                        errLogContent = errLogFile.read()
                        if verdict is Const.Verdict.WA:
                            errLogContent = "Produced = " + str(IOData.parseMulti(
                                iter(errLogContent.split("\n")),
                                self.config.returnType,
                                self.config.returnDimension))
                    logger.error(
                        "Solution '%s' produced wrong verdict %s on test #%d; Report: \n%s",
                        solutionName, verdict, i + 1, errLogContent)
                    del errLogContent
                    gc.collect()

            raise Errors.WrongSolutionFileCategory(
                "Solution '%s' does not worked as intended(%s)." %
                (solutionName, ",".join(str(s) for s in intendedCategories)))

        # Success, now let's remove error log.
        else:
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
        logger.info("Generating outputs for %s..",
                    "main AC only" if mainACOnly else "all solutions")
        AConly: typing.Tuple[Const.Verdict, ...] = (Const.Verdict.AC,)
        mainACModule: ExternalModule.AbstractExternalSolution = \
            self.solutionModules[AConly][0]
        answerFiles: typing.List[Path] = self.generateOutput(
            mainACModule, inputFiles, AConly, compare=False,
            solutionName="MAIN (%s)" %
            (formatPathForLog(self.config.solutions[AConly][0]),))

        # Constraint validation
        answers = []
        for i in range(len(answerFiles)):
            answerFile = answerFiles[i]
            try:
                answers.append(IOData.parseMulti(
                    IOData.yieldLines(answerFile),
                    self.config.returnType,
                    self.config.returnDimension))
                self.fs.pop(answerFile)
                gc.collect()
            except (ValueError, TypeError) as err:  # Produced wrong data
                logger.error("Main solution produced wrong data on #%d", i + 1)
                raise err.with_traceback(err.__traceback__)
        del answerFiles

        # Run all other solution files
        if not mainACOnly:
            for category in self.solutionModules:
                for i in range(len(self.solutionModules[category])):
                    module = self.solutionModules[category][i]
                    if module is mainACModule:
                        continue
                    result = self.generateOutput(
                        module, inputFiles, category, answers=answers,
                        solutionName=formatPathForLog(self.config.solutions[category][i]))
                    for outfilePath in result:  # Also remove outfiles
                        self.fs.pop(outfilePath)
                    gc.collect()

        # Return answer files
        gc.collect()
        return answers

    def runStressPipeline(
            self, stressTestIndex: int,
            batchSize: int = Const.DefaultBatchSize):
        """
        Run stress pipeline.
        """

        # Basic variables
        stress: dict = self.config.stresses[stressTestIndex]
        TL: float = stress["timelimit"]
        totalCount: int = stress["count"]
        modules: typing.List[ExternalModule.AbstractExternalSolution] = \
            [self.solutionModulesByPath[path] for path in stress["candidates"]]
        genscript: typing.List[str] = stress["genscript"]
        AConly: typing.Tuple[Const.Verdict, ...] = (Const.Verdict.AC,)

        # Generate genscripts
        genscripts: typing.List[typing.List[str]] = \
            [genscript[::] + [str(uuid.uuid4())] for _ in range(totalCount)]

        # Run batches
        currentIndex: int = 0
        batchCount: int = 0
        while currentIndex < totalCount:
            nextIndex = min(totalCount, currentIndex + batchSize)
            batchCount += 1
            logger.info("Running batch #%d..", batchCount)

            # Generate inputs
            inputFiles: typing.List[Path] = self.generateInput(
                genscripts[currentIndex:nextIndex])

            # Generate answers by jury
            answerFiles: typing.List[Path] = self.generateOutput(
                modules[0], inputFiles, AConly, compare=False,
                solutionName=modules[0].name, TL=TL)

            # Constraint validation
            answers = []
            for i in range(len(answerFiles)):
                answerFile = answerFiles[i]
                try:
                    answers.append(IOData.parseMulti(
                        IOData.yieldLines(answerFile),
                        self.config.returnType,
                        self.config.returnDimension))
                    self.fs.pop(answerFile)
                    gc.collect()
                except (ValueError, TypeError) as err:  # Produced wrong data
                    logger.error(
                        "Main solution produced wrong data on #%d", i + 1)
                    raise err.with_traceback(err.__traceback__)
            del answerFiles

            # Find malicious genscripts
            maliciousGenscripts: typing.Set[typing.Tuple[str, ...]] = set()
            for module in modules[1:]:
                verdicts: typing.List[Const.Verdict] = self.generateOutput(
                    module, inputFiles, AConly, compare=True, answers=answers,
                    solutionName=module.name, TL=TL, returnVerdicts=True)
                for i, verdict in enumerate(verdicts):
                    if verdict is not Const.Verdict.AC:
                        maliciousGenscripts.add(
                            tuple(genscripts[currentIndex + i]))

            if maliciousGenscripts:
                logger.error("Malicious genscripts found!")
                for maliciousGenscript in maliciousGenscripts:
                    logger.error(
                        "\"%s\" is malicious genscript",
                        " ".join(maliciousGenscript))
                raise Errors.AzadError("Malicious genscripts found")

            for inputFile in inputFiles:
                self.fs.pop(inputFile)
            currentIndex = nextIndex

        logger.info("Couldn't find any malicious genscript.")

    def writePGInFiles(self, inFiles: typing.List[Path]):
        """
        Read and convert parameters info PGized form into `self.config.IOPath`.
        """
        logger.info("Writing PGized input files..")
        for i in range(len(inFiles)):
            outPath = self.config.IOPath / \
                (self.config.inputFilePathSyntax % (i + 1,))
            logger.debug("Writing '%s'..", formatPathForLog(outPath))
            iterator = IOData.yieldLines(inFiles[i])
            data = [IOData.parseMulti(iterator, paramType, dimension)
                    for (_0, paramType, dimension) in self.config.parameters]
            with open(outPath, "wb") as outFile:
                outFile.write(b','.join(
                    IOData.PGizeData(e, t).encode('ascii')
                    for e, (_0, t, _2) in zip(data, self.config.parameters)))

    def writePGOutFiles(self, answers: list):
        """
        Convert answers into PGized form into `self.config.IOPath`.
        """
        logger.info("Writing PGized output files..")
        for i in range(len(answers)):
            outPath = self.config.IOPath / \
                (self.config.outputFilePathSyntax % (i + 1,))
            logger.debug("Writing '%s'..", formatPathForLog(outPath))
            with open(outPath, "wb") as outFile:
                outFile.write(IOData.PGizeData(
                    answers[i], self.config.returnType).encode('ascii'))

    def runRegularPipeline(self, produceDataOnly: bool = False):
        """
        Run regular pipeline.
        """

        # Go full or produce?
        inputDataFiles = self.generateInput(self.config.genscripts)
        self.validateInput(inputDataFiles)
        answers = self.generateOutputs(
            inputDataFiles, mainACOnly=produceDataOnly)
        logger.info("Generated all answers%s.",
                    " and validated all solutions"
                    if not produceDataOnly else "")

        # Write PGized I/O files
        IOData.cleanIOFilePath(self.config.IOPath)
        self.writePGInFiles(inputDataFiles)
        self.writePGOutFiles(answers)
        for file in inputDataFiles:
            self.fs.pop(file)
        logger.info("PG-transformed and wrote all data into files.")

    def run(self, mode: Const.AzadLibraryMode, stressTestIndex: int = 0):
        """
        Execute total pipeline with given mode.
        """
        if not isinstance(mode, Const.AzadLibraryMode):
            raise TypeError("Invalid mode type %s" % (type(mode),))

        # Generate external codes
        self.prepareModules()
        logger.info("Prepared all modules.")
        if mode is Const.AzadLibraryMode.GenerateCode:
            pause()
            return

        # Produce regular pipeline
        elif mode in (Const.AzadLibraryMode.Full, Const.AzadLibraryMode.Produce):
            self.runRegularPipeline(
                produceDataOnly=(mode is Const.AzadLibraryMode.Produce))

        # Produce stress-testing pipeline
        elif mode is Const.AzadLibraryMode.StressTest:
            self.runStressPipeline(stressTestIndex)

        else:
            raise ValueError("Invalid mode '%s'" % (mode,))
