"""
This module is core of Azad library.
"""

# Standard libraries
from copy import deepcopy
import json
import random
import hashlib
import os
from pathlib import Path
import importlib.util
import typing
import time
import atexit

# Azad libraries
from .constants import (
    SupportedConfigVersion,
    DefaultFloatPrecision, DefaultIOPath,
    DefaultInputSyntax, DefaultOutputSyntax,
    DefaultTimeLimit, DefaultMemoryLimit,  # Limits
    IODataTypesInfo, DefaultTypeStrings, MaxParameterDimensionAllowed,  # IO data types
    SolutionCategory, SourceFileLanguage, SourceFileType,  # Source file related
    ExitCodeSuccess, ExitCodeTLE, ExitCodeFailGeneral,  # Exit codes
    ExitCodeFailedInAVPhase, ExitCodeFailedToReturnData,
)
from .errors import (
    AzadError, FailedDataValidation, FailedDataGeneration,
    NotSupportedExtension, WrongSolutionFileCategory,
    VersionError, AzadTLE
)
from .externalmodule import (
    getExtension, getSourceFileLanguage,
    prepareModule_old, prepareExecFunc,
)
from .process import (
    AzadProcessGenerator, AzadProcessSolution, AzadProcessValidator,
)
from .iodata import (
    cleanIOFilePath, PGizeData,
    checkDataType, checkDataCompatibility,
    compareAnswers
)
from .logging import Logger
from .syntax import (
    variableNamePattern,
    cleanGenscript, generatorNamePattern,
    inputFilePattern, outputFilePattern,
)
from .misc import (longEndSkip,)


class AzadCore:
    """
    Azad library's core object generated from config.json
    """

    def __init__(self, configFilename: typing.Union[str, Path],
                 log: bool = True):

        # Get configuration JSON and move cwd to there
        if not isinstance(configFilename, (str, Path)):
            raise TypeError
        elif isinstance(configFilename, str):
            configFilename = Path(configFilename)
        with open(configFilename, "r") as configFile:
            parsedConfig: dict = json.load(configFile)
        self.configDirectory = configFilename.parent

        # Logger
        self.logger = Logger(self.configDirectory / "azadlib.log",
                             activated=log)
        self.logger.info("Current directory is %s" % (os.getcwd(),))
        self.logger.info("Target directory is %s" % (self.configDirectory,))
        self.logger.info("Analyzing configuration file..")

        # Version
        self.version = parsedConfig["version"]["config"]
        if not isinstance(self.version, (int, float)):
            raise TypeError(
                "Invalid type %s given for config version" % (type(self.version),))
        elif self.version < SupportedConfigVersion:
            raise VersionError("You are using older config version. "
                               "Please upgrade config file to %g" % (SupportedConfigVersion,))
        elif self.version > SupportedConfigVersion:
            self.logger.warn("You are using future config version(%g vs %g)" %
                             (self.version, SupportedConfigVersion))
        self.logger.info("This config file is v%g" % (self.version,))

        # Problem name and author
        self.logger.debug("Validating name, author and problem version..")
        self.problemName = parsedConfig["name"] if "name" in parsedConfig else None
        self.author = parsedConfig["author"] if "author" in parsedConfig else None
        self.problemVersion = parsedConfig["version"]["problem"] if "problem" in parsedConfig["version"] else 0.0
        self.logger.info("You opened '%s' v%g made by %s." %
                         (self.problemName, self.problemVersion, self.author))

        # Limits (Memory limit is currently unused)
        self.logger.debug("Validating limits and real number precision..")
        self.limits = {
            "time": float(parsedConfig["limits"]["time"]),
            "memory": int(parsedConfig["limits"]["memory"])}

        # Floating point precision
        self.floatPrecision = float(parsedConfig["precision"]) \
            if "precision" in parsedConfig else DefaultFloatPrecision
        if self.floatPrecision <= 0:
            raise ValueError("Non positive float precision")

        # Parameters
        self.logger.debug("Validating parameters..")
        self.parameters = {}  # {name: {order, typestr, dimension}}
        addedParameters = 0
        for obj in parsedConfig["parameters"]:
            varName, varType, dimension = \
                obj["name"], obj["type"], int(obj["dimension"])
            if not variableNamePattern.fullmatch(varName):
                raise SyntaxError(
                    "Parameter name %s failed syntax" % (varName,))
            elif varName in self.parameters:
                raise ValueError(
                    "Parameter name %s occurred multiple times" % (varName,))
            elif varType not in IODataTypesInfo:
                raise ValueError("Parameter %s's type is invalid type '%s'" %
                                 (varName, varType))
            elif not (0 <= dimension <= MaxParameterDimensionAllowed):
                raise ValueError("Invalid dimension %d for parameter %s given" %
                                 (dimension, varName))
            self.parameters[varName] = {
                "order": addedParameters, "type": varType, "dimension": dimension}
            addedParameters += 1
        self.parameterNamesSorted = [name for name in self.parameters]
        self.parameterNamesSorted.sort(
            key=lambda x: self.parameters[x]["order"])

        # Return value
        self.logger.debug("Validating return value..")
        returnVarType = parsedConfig["return"]["type"]
        if returnVarType not in IODataTypesInfo:
            raise ValueError(
                "Return value type '%s' is invalid" % (returnVarType,))
        returnDimension = int(parsedConfig["return"]["dimension"])
        self.returnValueInfo = {"type": returnVarType,
                                "dimension": returnDimension}

        # I/O files
        self.logger.debug("Validating I/O file path..")
        try:
            self.IOPath: Path = self.configDirectory / \
                parsedConfig["iofiles"]["path"]
            self.inputFilePathSyntax: str = parsedConfig["iofiles"]["inputsyntax"]
            self.outputFilePathSyntax: str = parsedConfig["iofiles"]["outputsyntax"]
        except NameError as err:
            self.IOPath: Path = self.configDirectory / DefaultIOPath
            self.inputFilePathSyntax: str = DefaultInputSyntax
            self.outputFilePathSyntax: str = DefaultOutputSyntax
        if not self.IOPath.exists():
            os.mkdir(self.IOPath)
        elif tuple(self.IOPath.iterdir()):
            self.logger.warn(
                "Given IOPath '%s' is not empty directory" %
                (self.IOPath,))
        elif not inputFilePattern.fullmatch(self.inputFilePathSyntax):
            raise SyntaxError(
                "Input file syntax '%s' doesn't match syntax" %
                (self.inputFilePathSyntax))
        elif not outputFilePattern.fullmatch(self.outputFilePathSyntax):
            raise SyntaxError(
                "Output file syntax '%s' doesn't match syntax" %
                (self.outputFilePathSyntax,))

        # Solution files
        self.logger.debug("Validating solution files..")
        self.solutions = {}
        for category in SolutionCategory:
            if category.value not in parsedConfig["solutions"]:
                self.solutions[category] = []
            else:
                self.solutions[category] = [
                    self.configDirectory / v for v in parsedConfig["solutions"][category.value]]
                for p in self.solutions[category]:
                    if not p.is_file():
                        raise FileNotFoundError(
                            "Solution '%s'(%s) is not a file" % (p, category.value))
        if not self.solutions[SolutionCategory.AC]:
            self.logger.warn("There is no AC solution.")

        # Generators
        self.logger.debug("Validating generator files..")
        self.generators = parsedConfig["generators"]
        if not isinstance(self.generators, dict):
            raise TypeError("Invalid generators type %s given in config." % (
                type(self.generators),))
        for generatorName in self.generators:
            if not generatorNamePattern.fullmatch(generatorName):
                raise SyntaxError(
                    "Generator name '%s' doesn't match pattern" % (generatorName,))
            genFile = self.configDirectory / self.generators[generatorName]
            if not genFile.exists() or not genFile.is_file():
                raise FileNotFoundError(
                    "Generator file '%s' not found" % (genFile,))
            else:
                self.generators[generatorName] = genFile

        # Generator script (genscript)
        self.logger.debug("Validating generator script(genscript)..")
        if not isinstance(parsedConfig["genscript"], (list, tuple)):
            raise TypeError("Invalid genscript type %s given in config." %
                            (type(parsedConfig["genscript"]),))
        self.genScripts = cleanGenscript(
            parsedConfig["genscript"], self.generators.keys())
        if not self.genScripts:
            self.logger.warn("There is no genscript.")

        # Validator
        self.logger.debug("Validating validator file..")
        self.validator = parsedConfig["validator"].strip()
        if not self.validator:
            self.logger.warn("There is no validator.")
        elif not Path(self.validator).exists():
            raise FileNotFoundError(
                "Validator file '%s' not found" % (self.validator,))

        # Inner attributes and flags
        self.producedAnswers = []
        self.inputDatas = []

        # Reserve termination
        atexit.register(self.terminate)

    def terminate(self):
        """
        Terminate.
        """
        self.logger.info("Terminating Azad core..")
        del self.producedAnswers
        del self.inputDatas
        # self.logger.terminate()  # Log file will be auto terminated

    def executeValidator(
            self, sourceFilePath: typing.Union[str, Path], data=None):
        """
        Execute sourcefile as validator by given file name.
        Validate input file.
        """
        # Generate data, if not available
        if data is None:
            if not self.inputDatas:
                self.inputDatas = self.generateInput(validate=False)
            data = self.inputDatas

        # Run multiprocessing
        startTime = time.perf_counter()
        processes = [
            AzadProcessValidator(
                sourceFilePath,
                args=[deepcopy(data[i][varName])
                      for varName in self.parameterNamesSorted],
                timelimit=5.0,
            ) for i in range(len(data))
        ]
        for i in range(len(data)):
            self.logger.debug("Validation process #%d started.." % (i + 1,))
            processes[i].start()
        for i in range(len(data)):
            self.logger.info("Waiting validation process #%d.." % (i + 1,))
            processes[i].join()

        # Analyze results
        for i in range(len(data)):
            self.logger.debug("Analyzing validation process #%d.." % (i + 1,))
            if processes[i].exitcode == ExitCodeSuccess:
                self.logger.debug("Ok, validation passed.")
            elif processes[i].exitcode == ExitCodeTLE:
                raise AzadTLE("Validation process #%d got TLE" % (i + 1,))
            elif processes[i].exitcode == ExitCodeFailGeneral:
                self.logger.error(
                    "Validation process #%d raised an error:\n%s" %
                    (i + 1, processes[i].raisedTraceback), maxlen=2000)
                raise FailedDataValidation
            else:
                raise FailedDataValidation(
                    "Validation process #%d with unknown reason (Exit code %d)" %
                    (i + 1, processes[i].exitcode))

        # Check performance
        endTime = time.perf_counter()
        self.logger.info(
            "Validated all data in %g seconds." % (endTime - startTime,))

    def generateInput(self, validate: bool = True) -> list:
        """
        Generate all input data and return.
        """
        if not self.genScripts:
            raise ValueError("There is no genscript")
        self.logger.info("Generating input data..")
        startTime = time.perf_counter()

        # Execute genscripts with multiprocessing.
        # Suppose all genscript lines are validated before.
        processes = []
        for i in range(len(self.genScripts)):
            genscript = self.genScripts[i]
            elements = genscript.split(" ")
            genFilePath = self.generators[elements[0]]
            args = elements[1:]
            self.logger.debug("Starting generation process #%d, genscript = '%s'.." %
                              (i + 1, genscript))
            processes.append(AzadProcessGenerator(
                genFilePath, args, self.parameters, timelimit=5.0))
            processes[-1].start()
        for i in range(len(self.genScripts)):
            self.logger.info("Waiting generation process #%d.." % (i + 1,))
            processes[i].join()

        # Analyze results
        result = []
        for i in range(len(self.genScripts)):
            self.logger.debug("Analyzing generation process #%d.." % (i + 1,))
            if processes[i].exitcode == ExitCodeSuccess:
                result.append(processes[i].returnedValue)
            elif processes[i].exitcode == ExitCodeFailedInAVPhase:
                self.logger.error(
                    "Generation process #%d generated wrong data:\n%s" %
                    (i + 1, processes[i].raisedTraceback), maxlen=2000)
                raise FailedDataGeneration
            elif processes[i].exitcode == ExitCodeTLE:
                raise FailedDataGeneration(
                    "Generation process #%d got TLE" % (i + 1,))
            elif processes[i].exitcode == ExitCodeFailGeneral:
                self.logger.error(
                    "Generation process #%d raised an exception during generation:\n%s" %
                    (i + 1, processes[i].raisedTraceback), maxlen=2000)
                raise FailedDataGeneration
            else:
                raise FailedDataGeneration(
                    "Generation process #%d failed with unknown reason (Exit code %d)" %
                    (i + 1, processes[i].exitcode))

        # Check performance
        endTime = time.perf_counter()
        self.logger.info(
            "Generated all data in %g seconds." % (endTime - startTime,))

        # If there is an validator then validate it
        if self.validator and validate:
            self.executeValidator(self.validator, result)
        return result

    def executeSolution(self, sourceFilePath: typing.Union[str, Path],
                        intendedCategory: SolutionCategory = SolutionCategory.AC,
                        mainAC: bool = False) -> list:
        """
        Execute sourcefile as solution by given file name.
        Validate result and category, and return produced answers.
        If `mainAC` is True, then doesn't check answers and just return.
        """

        # Validate parameters
        if sourceFilePath not in self.solutions[intendedCategory]:
            self.logger.warn(
                "You are trying to execute non-registered solution file '%s' (%s)" %
                (sourceFilePath, intendedCategory.value))
        if not isinstance(intendedCategory, SolutionCategory):
            raise TypeError("Invalid type %s given for category" %
                            (type(intendedCategory),))
        elif intendedCategory is not SolutionCategory.AC and mainAC:
            raise ValueError("Category is %s but mainAC is True" %
                             (intendedCategory.value,))

        # Generate data. If input data is empty, then generation is forced.
        if not self.inputDatas:
            self.inputDatas = self.generateInput(validate=True)

        # Do multiprocessing
        self.logger.info("Analyzing solution '%s'.." % (sourceFilePath,))
        startTime = time.perf_counter()
        verdicts = []
        producedAnswers = []
        processes = [AzadProcessSolution(
            sourceFilePath, self.returnValueInfo,
            args=deepcopy([self.inputDatas[i][varName]
                           for varName in self.parameterNamesSorted]),
            timelimit=self.limits["time"]
        ) for i in range(len(self.inputDatas))]
        for i in range(len(self.inputDatas)):
            self.logger.debug("Starting solution process #%d.." % (i + 1,))
            processes[i].start()
        for i in range(len(self.inputDatas)):
            self.logger.info("Waiting solution process #%d.." % (i + 1,))
            processes[i].join()
        for i in range(len(self.inputDatas)):
            self.logger.debug("Analyzing solution process #%d.." % (i + 1,))
            if processes[i].exitcode == ExitCodeSuccess:
                # I will implement customized checker,
                # this is why I separated answer checking from multiprocessing.
                thisAnswer = processes[i].returnedValue
                producedAnswers.append(thisAnswer)
                if mainAC or compareAnswers(
                        self.producedAnswers[i], thisAnswer,
                        floatPrecision=self.floatPrecision):
                    verdicts.append(SolutionCategory.AC)
                else:
                    verdicts.append(SolutionCategory.WA)
            else:
                producedAnswers.append(None)
                if processes[i].exitcode == ExitCodeTLE:
                    verdicts.append(SolutionCategory.TLE)
                else:
                    verdicts.append(SolutionCategory.FAIL)
            self.logger.debug("Solution '%s' got %s at test #%d." %
                              (sourceFilePath.parts[-1],
                               verdicts[-1].value.upper(), i + 1))

        # Validate verdicts
        endTime = time.perf_counter()
        self.logger.info(
            "Executed solution for all data in %g seconds." %
            (endTime - startTime,))
        self.logger.info("Answers = %s" % (producedAnswers,))
        verdictCounts = {category: verdicts.count(category)
                         for category in SolutionCategory}
        self.logger.info("Solution '%s' verdict: %s" %
                         (sourceFilePath.parts[-1],
                          {key.value.upper(): verdictCounts[key]
                              for key in verdictCounts}))
        nonACPriorities = [
            SolutionCategory.FAIL, SolutionCategory.WA, SolutionCategory.TLE]
        for verdict in nonACPriorities:
            if verdictCounts[verdict] > 0:
                actualCategory = verdict
                break
        else:
            actualCategory = SolutionCategory.AC

        # Return
        if actualCategory is not intendedCategory:
            raise WrongSolutionFileCategory(
                sourceFilePath, intendedCategory, actualCategory)
        return producedAnswers

        # Return produced answers
        return producedAnswers

    def makeInputFiles(self, inputFileSyntax: str = None):
        """
        Make input files from generated input data.
        """
        if not inputFileSyntax:
            inputFileSyntax = self.inputFilePathSyntax
        elif not inputFilePattern.fullmatch(inputFileSyntax):
            raise SyntaxError
        self.logger.info("Making input files '%s/%s..'" %
                         (self.IOPath, inputFileSyntax))
        cleanIOFilePath(self.IOPath, [".in.txt"])
        if not self.inputDatas:
            self.inputDatas = self.generateInput()
        i = 0
        for data in self.inputDatas:
            i += 1
            with open(self.IOPath / (inputFileSyntax % (i,)), "w") as inputFile:
                self.logger.debug(
                    "Writing %d-th input file '%s'.." %
                    (i, inputFile.name))
                inputFile.write(",".join(
                    PGizeData(data[name], self.parameters[name]["type"])
                    for name in self.parameterNamesSorted))

    def makeOutputFiles(self, outputFileSyntax: str = None):
        """
        Make output files from produced answer data.
        """
        if not outputFileSyntax:
            outputFileSyntax = self.outputFilePathSyntax
        elif not outputFilePattern.fullmatch(outputFileSyntax):
            raise SyntaxError
        self.logger.info("Making output files '%s/%s..'" %
                         (self.IOPath, outputFileSyntax))
        cleanIOFilePath(self.IOPath, [".out.txt"])
        if not self.producedAnswers:
            self.logger.warn("Answer is not produced yet. Producing first..")
            self.producedAnswers = self.executeSolution(
                self.solutions[SolutionCategory.AC][0], SolutionCategory.AC, mainAC=True)
            if not self.producedAnswers:
                raise AzadError("Answer data cannot be produced")
        i = 0
        for data in self.producedAnswers:
            i += 1
            with open(self.IOPath / (outputFileSyntax % (i,)), "w") as outputFile:
                self.logger.debug(
                    "Writing %d-th output file '%s'.." %
                    (i, outputFile.name))
                outputFile.write(PGizeData(data, self.returnValueInfo["type"]))

    def checkAllSolutionFiles(self):
        """
        Check all solution files.
        """
        if not self.solutions[SolutionCategory.AC]:
            raise AzadError("There is no AC solution")
        self.logger.info("Checking all solution files..")
        self.producedAnswers = self.executeSolution(
            self.solutions[SolutionCategory.AC][0], SolutionCategory.AC, mainAC=True)
        for filePath in self.solutions[SolutionCategory.AC][1:]:
            self.executeSolution(filePath, SolutionCategory.AC)
        for category in SolutionCategory:
            if category is SolutionCategory.AC:
                continue
            for filePath in self.solutions[category]:
                self.executeSolution(filePath, category)
