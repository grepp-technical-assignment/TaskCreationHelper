"""
This module helps to parse config easily.
"""

# Standard libraries
import logging
from pathlib import Path
import warnings
import typing

logger = logging.getLogger(__name__)

# Azad libraries
from . import constants as Const, syntax as Syntax
from .misc import setupLoggers, isExistingFile
from .errors import AzadError, VersionError


class TaskConfiguration:
    """
    Information of task configuration.
    Parse `config.json` by passing json object to initializer.
    """

    def __init__(
            self, cwd: Path, *args,
            log: str = None, resetRootLoggerConfig: bool = True,
            version: dict = None,
            name: str = None, author: str = None,
            limits: dict = None,
            precision: typing.Union[str, float] = Const.DefaultFloatPrecision,
            parameters: typing.List[dict],
            iofiles: dict = None,
            solutions: dict = None, generators: dict = None,
            genscript: typing.List[str] = (),
            validator: Path = None,
            **kwargs):

        # Log file
        self.directory = cwd
        self.logFilePath = self.directory / \
            (log if log else Const.DefaultLoggingFileName)
        with open(self.logFilePath, "a") as mainLogFile:
            mainLogFile.write("\n" + "=" * 240 + "\n\n")
        setupLoggers(self.logFilePath, resetRootLoggerConfig,
                     mainProcess=True, noStreamHandler=False)
        logger.info("Constructing configuration from given file...")
        logger.info("Basic path is '%s'", cwd)

        # Version
        logger.debug("Validating config version..")
        if version is None:
            raise ValueError("Version is none")
        self.configVersion = version["config"]
        if not isinstance(self.configVersion, (int, float)):
            raise TypeError(
                "Invalid type %s given for config version" %
                (type(self.configVersion),))
        elif self.configVersion < Const.SupportedConfigVersion:
            raise VersionError("You are using older config version. "
                               "Please upgrade config file to %g" %
                               (Const.SupportedConfigVersion,))
        elif self.configVersion > Const.SupportedConfigVersion:
            warnings.warn("You are using future config version(%g vs %g)" %
                          (self.configVersion, Const.SupportedConfigVersion))
        logger.info("This config file's version is v%g", self.configVersion)

        # Problem name and author
        self.name: str = name
        self.author: str = author
        self.problemVersion = version["problem"] if "problem" in version else None

        # Limits
        logger.debug("Validating limits..")
        if not isinstance(limits, dict) or \
                not set(limits.keys()).issubset({"time", "memory"}):
            raise ValueError
        self.TL: float = float(limits["time"]) if "time" in limits \
            else Const.DefaultTimeLimit
        if self.TL <= 0:
            raise ValueError("Non-positive time limit")
        elif self.TL < 1:
            warnings.warn("Too low time limit %gs" % (self.TL,))
        self.ML: float = float(limits["memory"]) if "memory" in limits \
            else Const.DefaultMemoryLimit
        if self.ML <= 0:
            raise ValueError("Non-positive memory limit")
        elif self.ML < 256:
            warnings.warn("Too low memory limit %gMB" % (self.ML,))

        # Floating point precision
        self.floatPrecision = float(precision)

        # Parameters: [(name, iovt, dimension), ..]
        logger.debug("Validating parameters..")
        self.parameters: typing.List[str, Const.IOVariableTypes, int] = []
        for obj in parameters:
            if not isinstance(obj, dict):
                raise TypeError
            elif set(obj.keys()) != {"name", "type", "dimension"}:
                raise ValueError("Invalid keys")
            varName, varType, dimension = obj["name"], \
                Const.getIOVariableType(obj["type"]), int(obj["dimension"])
            if varName in [p[0] for p in self.parameters]:
                raise ValueError(
                    "Parameter name %s occurred multiple times" %
                    (varName,))
            elif not (0 <= dimension <= Const.MaxParameterDimensionAllowed):
                raise ValueError("Invalid dimension %d in parameter %s" %
                                 (dimension, varName))
            self.parameters.append((varName, varType, dimension))

        # Return value
        logger.debug("Validating return info..")
        if "return" not in kwargs:
            raise KeyError("Return value info should be provided")
        elif not isinstance(kwargs["return"], dict):
            raise TypeError
        self.returnType = Const.getIOVariableType(kwargs["return"]["type"])
        self.returnDimension = int(kwargs["return"]["dimension"])
        if not (0 <= self.returnDimension <=
                Const.MaxParameterDimensionAllowed):
            raise ValueError("Invalid return dimension %d" %
                             (self.returnDimension,))

        # I/O files
        logger.debug("Validating I/O file path..")
        try:
            if not isinstance(iofiles, dict):
                raise TypeError
            self.IOPath: Path = cwd / iofiles["path"]
            self.inputFilePathSyntax = iofiles["inputsyntax"]
            self.outputFilePathSyntax = iofiles["outputsyntax"]
        except (TypeError, KeyError):
            self.IOPath: Path = cwd / Const.DefaultIOPath
            self.inputFilePathSyntax = Const.DefaultInputSyntax
            self.outputFilePathSyntax = Const.DefaultOutputSyntax
        if not self.IOPath.exists():
            self.IOPath.mkdir()
        elif tuple(self.IOPath.iterdir()):
            warnings.warn("Given IOPath '%s' is not empty" % (self.IOPath,))
        elif not Syntax.inputFilePattern.fullmatch(self.inputFilePathSyntax):
            raise SyntaxError
        elif not Syntax.outputFilePattern.fullmatch(self.outputFilePathSyntax):
            raise SyntaxError

        # Solution files
        logger.debug("Validating solution files..")
        self.solutions: typing.Mapping[
            typing.Tuple[Const.Verdict, ...],
            typing.List[Path]] = {}
        if not isinstance(solutions, dict):
            raise TypeError("Solutions should be provided")
        for key in solutions:
            thisCategories = tuple(sorted(set(
                Const.getSolutionCategory(word.strip())
                for word in key.split("/")), key=lambda x: x.name))
            if thisCategories not in self.solutions:
                self.solutions[thisCategories] = []
            for p in solutions[key]:
                path = cwd / p
                if not isExistingFile(path):
                    raise FileNotFoundError(
                        "Solution '%s' (%s) doesn't exists" %
                        (path, ",".join(c.name for c in thisCategories)))
                else:
                    self.solutions[thisCategories].append(path)
        if (Const.Verdict.AC,) not in self.solutions or \
                not self.solutions[(Const.Verdict.AC, )]:
            raise AzadError("There is no main AC solution")

        # Generators
        logger.debug("Validating generator files..")
        self.generators: typing.Mapping[str, Path] = \
            generators if isinstance(generators, dict) else {}
        if not self.generators:
            raise ValueError("There is no generator registered")
        for generatorName in tuple(self.generators.keys()):
            if not Syntax.generatorNamePattern.fullmatch(generatorName):
                raise SyntaxError(
                    "Generator name '%s' doesn't satisfy syntax" % (generatorName,))
            genFile = cwd / self.generators[generatorName]
            if not isExistingFile(genFile):
                raise FileNotFoundError(
                    "Generator file '%s' not found" % (genFile,))
            else:
                self.generators[generatorName] = genFile

        # Generator script (genscript)
        logger.debug("Validating genscript..")
        if not isinstance(genscript, (list, tuple)):
            raise TypeError
        self.genscripts = [Syntax.cleanGenscript(line, self.generators.keys())
                           for line in genscript]
        self.genscripts: typing.List[typing.List[str]] = \
            [x for x in self.genscripts if x]
        if not self.genscripts:
            raise ValueError("There is no non-commented genscript.")

        # Validator
        logger.debug("Validating validator file..")
        self.validator = (cwd / Path(validator)) if validator else None
        if self.validator is None:
            warnings.warn("There is no validator.")
