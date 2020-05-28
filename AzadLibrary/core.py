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
import atexit

# Azad libraries
from .constants import (
    SupportedConfigVersion,
    DefaultFloatPrecision, DefaultIOPath,
    DefaultInputSyntax, DefaultOutputSyntax,
    DefaultTimeLimit, DefaultMemoryLimit,  # Limits
    IODataTypesInfo, DefaultTypeStrings,  # IO data types
    SolutionCategory, SourceFileLanguage,  # Source file related
)
from .errors import (
    AzadError, FailedDataValidation, NotSupportedExtension,
    WrongSolutionFileCategory, VersionError
)
from .path import (getExtension, getSourceFileLanguage)
from .iodata import (
    cleanIOFilePath, YBMBizeData,
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
        self.limits = {"time": float(parsedConfig["limits"]["time"]), "memory": int(
            parsedConfig["limits"]["memory"])}

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
        self.returnValue = {"type": returnVarType,
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

    @staticmethod
    def prepareModule(sourceFilePath: typing.Union[str, Path],
                      moduleName: str):
        """
        Prepare module from given file name.
        """
        # Get filename extension
        fileExtension = getExtension(sourceFilePath)
        sourceLanguage = getSourceFileLanguage(sourceFilePath)

        # Extension case handling
        if sourceLanguage is SourceFileLanguage.Python3:
            spec = importlib.util.spec_from_file_location(
                moduleName, sourceFilePath)
            thisModule = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(thisModule)
            return thisModule
        else:
            raise NotImplementedError(
                "Extension '%s' is not supported" % (fileExtension,))

    def executeValidator(
            self, sourceFilePath: typing.Union[str, Path], data=None):
        """
        Execute sourcefile as validator by given file name.
        Validate input file.
        """

        # Generate data, if not available
        if data is None:
            if not self.inputDatas:
                self.inputDatas = self.generateInput()
            data = self.inputDatas

        # Pop validator function
        validation = None
        sourceModule = AzadCore.prepareModule(sourceFilePath, "validator")
        sourceLanguage = getSourceFileLanguage(sourceFilePath)
        if sourceLanguage is SourceFileLanguage.Python3:
            validation = sourceModule.validate
        else:
            raise NotSupportedExtension(getExtension(sourceFilePath))
        if not validation:
            raise AzadError(
                "Validation function is invalid in '%s'" %
                (sourceFilePath,))

        # Validate input
        self.logger.info("Validating input by '%s'.." % (sourceFilePath,))
        i = 0
        for inputData in data:
            i += 1
            self.logger.info("Validating %d-th input.." % (i,))
            try:
                validation(*[deepcopy(inputData[varName])
                             for varName in self.parameterNamesSorted])
            except Exception as err:
                self.logger.error(
                    "Validation failed at %d-th input. (%s)" %
                    (i, type(err)))
                if err.args:
                    self.logger.error("Detail log: \"%s\"" %
                                      (" ".join(err.args),))
                raise FailedDataValidation().with_traceback(err.__traceback__)
            else:
                self.logger.debug("Validated %d-th input." % (i,))

    def executeGenerator(
            self, sourceFilePath: typing.Union[str, Path], args: typing.Tuple[str]) -> dict:
        """
        Execute generator with given arguments. args is tuple of strings.
        You have to make function `generate(args: string[])` to generate data.
        Generator's return value form should be `{variable name: content}`.
        """
        # Prepare module
        generateModule = AzadCore.prepareModule(sourceFilePath, "generator")
        genFunc = None
        sourceLanguage = getSourceFileLanguage(sourceFilePath)
        if sourceLanguage is SourceFileLanguage.Python3:
            genFunc = generateModule.generate
        else:
            fileExtension = getExtension(sourceFilePath)
            raise NotSupportedExtension(fileExtension)
        if not genFunc:
            raise FailedDataValidation("Generating function is invalid")

        # Execution
        hashValue = hashlib.sha256("|".join(args).encode()).hexdigest()
        random.seed(hashValue)
        self.logger.debug("Executing genscript '%s' on '%s', hash = '%s..'" %
                          (" ".join(args), sourceFilePath.name, longEndSkip(hashValue, 20)))
        result = genFunc(args)
        self.logger.debug("Result is %s" % (result,), maxlen=500)

        # Analyze execution result
        if not isinstance(result, dict):
            raise FailedDataValidation("Generator '%s' generated %s instead of dict" %
                                       (sourceFilePath, type(result),))
        elif set(result.keys()) != set(self.parameters.keys()):
            raise FailedDataValidation("Generator '%s' generated different parameters (%s)" %
                                       (sourceFilePath, ", ".join(result.keys()),))
        self.logger.debug(
            "Validating generated data's parameter types and compatibility..")
        for name in result:
            if not checkDataType(result[name], self.parameters[name]["type"],
                                 self.parameters[name]["dimension"], variableName=name):
                raise FailedDataValidation(
                    "Generator '%s' generated wrong type for parameter %s on args %s" %
                    (sourceFilePath, name, args))
            elif not checkDataCompatibility(result[name], self.parameters[name]["type"]):
                raise FailedDataValidation(
                    "Generator '%s' generated incompatible %s data for parameter %s on args %s" %
                    (sourceFilePath, self.parameters[name]["type"], name, args))
        return result

    def generateInput(self) -> list:
        """
        Generate all input data and return.
        """
        if not self.genScripts:
            raise ValueError("There is no genscript")
        self.logger.info("Generating input data..")

        # Execute gen scripts:
        # Suppose all genscript lines are validated in __init__.
        result = []
        i = 0
        for script in self.genScripts:
            elements = script.split(" ")
            genFilePath = self.generators[elements[0]]
            i += 1
            self.logger.info("Generating input data #%d.." % (i,))
            result.append(self.executeGenerator(genFilePath, elements[1:]))

        # If no data produced then raise error
        if not result:
            raise FailedDataValidation("No input data generated")
        else:
            if self.validator:
                self.executeValidator(self.validator, result)
            return result

    def executeSolution(self, sourceFilePath: typing.Union[str, Path],
                        intendedCategory: SolutionCategory = SolutionCategory.AC,
                        mainAC: bool = False) -> list:
        """
        Execute sourcefile as solution by given file name.
        Validate result and category, and return produced answers.
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
            self.inputDatas = self.generateInput()

        # Pop solution functions
        solution = None
        sourceModule = AzadCore.prepareModule(sourceFilePath, "submission")
        sourceLanguage = getSourceFileLanguage(sourceFilePath)
        if sourceLanguage is SourceFileLanguage.Python3:
            solution = sourceModule.solution
        else:
            raise NotSupportedExtension(getExtension(sourceFilePath))
        if not solution:
            raise AzadError("Solution function is invalid in '%s'" %
                            (sourceFilePath,))

        # Actual invocation
        self.logger.info(
            "Executing solution '%s' for %s.." %
            (sourceFilePath, intendedCategory.value.upper() + (" (MAIN)" if mainAC else "")))
        varNamesSorted = list(self.parameters.keys())
        varNamesSorted.sort(key=lambda x: self.parameters[x]["order"])
        producedAnswers = []
        verdicts = [None for _ in range(len(self.inputDatas))]
        i = 0
        for inputData in self.inputDatas:
            i += 1
            self.logger.info("Running %d-th test case.." % (i,))
            try:
                result = solution(*[deepcopy(inputData[varName])
                                    for varName in varNamesSorted])
                if not checkDataType(
                        result, self.returnValue["type"],
                        self.returnValue["dimension"], "return value"):
                    raise FailedDataValidation(
                        "Solution %s generated wrong type of data on %d-th testcase" %
                        (sourceFilePath, i))
                elif not checkDataCompatibility(result, self.returnValue["type"]):
                    raise FailedDataValidation(
                        "Solution %s generated incompatible %s data on %d-th testcase" %
                        (sourceFilePath, self.returnValue["type"], i))

            except (TimeoutError, MemoryError, RuntimeError, FailedDataValidation) as err:  # Error raised
                actualCategory = SolutionCategory.FAIL
                if isinstance(err, TimeoutError):
                    actualCategory = SolutionCategory.TLE
                elif isinstance(err, MemoryError):
                    # Memory error is not supported, but accepted
                    pass
                else:  # General error
                    pass
                verdicts[i - 1] = actualCategory

                # Case handling
                if mainAC:
                    raise AzadError(
                        "Main AC solution got %s" % (actualCategory.value.upper(),))
                else:
                    self.logger.debug(
                        "Solution '%s' got %s on test #%d, which is intended." %
                        (sourceFilePath, intendedCategory.value.upper(), i))

                # Add dummy value anyway
                producedAnswers.append(None)

            else:  # Produced data well. Check return data type.
                producedAnswers.append(result)

        # Do job with total produced answers
        if not mainAC:

            # Iterate over answer comparisons
            for i in range(len(producedAnswers)):
                if verdicts[i] is not None and producedAnswers[i] is None:  # Already verdicted
                    continue
                self.logger.debug(
                    "Comparing %d-th produced answer.. (%s vs %s)" %
                    (i + 1, self.producedAnswers[i], producedAnswers[i]))
                gotAC = compareAnswers(
                    self.producedAnswers[i], producedAnswers[i],
                    floatPrecision=self.floatPrecision)
                self.logger.debug("Verdict is %s" % ("AC" if gotAC else "WA",))
                verdicts[i] = SolutionCategory.AC if gotAC else SolutionCategory.WA
            verdictCount = {
                intendedCategory: 0 for intendedCategory in SolutionCategory}
            for verdict in verdicts:
                verdictCount[verdict] += 1
            self.logger.debug("Solution '%s' (Intended to be %s): %s" %
                              (sourceFilePath, intendedCategory.value.upper(),
                               ", ".join("%d %s" % (verdictCount[verdict], verdict.value.upper()) for verdict in verdictCount)))

            # Validate total result.
            # intendedCategory is already validated before.
            actualVerdict: SolutionCategory = None
            if verdictCount[SolutionCategory.AC] == len(producedAnswers):
                actualVerdict = SolutionCategory.AC
            elif verdictCount[SolutionCategory.FAIL] > 0:
                actualVerdict = SolutionCategory.FAIL
            elif verdictCount[SolutionCategory.WA] == 0:
                actualVerdict = SolutionCategory.TLE
            else:
                actualVerdict = SolutionCategory.WA
            if actualVerdict != intendedCategory:
                raise WrongSolutionFileCategory(
                    sourceFilePath, intendedCategory, actualVerdict)
            else:
                self.logger.info(
                    "Solution '%s' worked as intended %s." %
                    (sourceFilePath, intendedCategory.value.upper()))

        else:  # If mainAC is True, then automatically copy producedAnswers.
            self.logger.debug("Making produced answers as official..")
            self.producedAnswers = producedAnswers

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
                    YBMBizeData(data[name], self.parameters[name]["type"])
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
                outputFile.write(YBMBizeData(data, self.returnValue["type"]))

    def checkAllSolutionFiles(self):
        """
        Check all solution files.
        """
        if not self.solutions[SolutionCategory.AC]:
            raise AzadError("There is no AC solution")
        self.logger.info("Checking all solution files..")
        self.executeSolution(
            self.solutions[SolutionCategory.AC][0], SolutionCategory.AC, mainAC=True)
        for filePath in self.solutions[SolutionCategory.AC][1:]:
            self.executeSolution(filePath, SolutionCategory.AC)
        for category in SolutionCategory:
            if category is SolutionCategory.AC:
                continue
            for filePath in self.solutions[category]:
                self.executeSolution(filePath, category)
