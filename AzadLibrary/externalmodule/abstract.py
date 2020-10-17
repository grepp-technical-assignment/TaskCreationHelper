"""
This module provides abstract base interface of code generator.
"""

# Standard libraries
import typing
from pathlib import Path
from subprocess import Popen, DEVNULL, TimeoutExpired
from string import Template as StringTemplate
import logging

logger = logging.getLogger(__name__)

# Azad libraries
from .. import constants as Const
from ..filesystem import TempFileSystem
from ..misc import isExistingFile, limitSubprocessResource
from ..errors import AzadError


class AbstractProgrammingLanguage:
    """
    Abstract base of programming language for external module.
    """

    # Default indentation
    defaultIndentation = 4

    # typeStrTable[IOVT][dimension] is corresponding type in language.
    baseTypeStrTable = {iovt: NotImplemented for iovt in Const.IOVariableTypes}

    @classmethod
    def typeStr(cls, iovt: Const.IOVariableTypes, dimension: int):
        """
        Return type string for given iovt and dimension.
        """
        raise NotImplementedError

    # Module template files; Should be overrided in child class.
    generatorTemplatePath = NotImplemented
    solutionTemplatePath = NotImplemented
    validatorTemplatePath = NotImplemented

    @classmethod
    def leveledNewline(cls, level: int) -> str:
        """
        Return separator used for multiple lines of codes.
        The reason why this method is classmethod is because
        default indentation can be different by languages.
        """
        return "\n" + (" " * level * cls.defaultIndentation)

    @classmethod
    def multipleCodelines(cls, level: int, *lines: typing.List[str]) -> str:
        """
        Generate multiple lines of code for convenience.
        """
        return cls.leveledNewline(level).join(lines)

    @classmethod
    def templateDict(cls, *args, **kwargs) -> dict:
        """
        Return dictionary to replace generated code.
        Be aware that some arguments passed by `kwargs`
        may be replaced in child class method.
        """
        result = {"ExitCode" + v.name: v.value
                  for v in Const.ExitCode}
        result.update(**kwargs)
        return result

    @classmethod
    def generateCodeInitParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        """
        Return statement `pType varName;`
        """
        raise NotImplementedError

    @classmethod
    def generateCodeGetParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        """
        Return statement `pType varName = TCHIO.get(...);`.
        """
        raise NotImplementedError

    @classmethod
    def generateCodePutParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        """
        Return statement `TCHIO.print(varName);`.
        """
        raise NotImplementedError


class AbstractExternalModule:
    """
    Abstract base of all external modules.
    When you inherit and make new modules, please inherit like
    `class NewLanguage$Filetype($AbstractFiletype, $AbstractLang): ...`.

    Stream `stdout` is set to `DEVNULL` in subprocess
    for all external modules for better performance.

    `originalModulePath` is NOT a real original module path here,
    it's meant to be COPIED module's path. `self.executable` or
    `self.modulePath` will be executed.
    """

    def __init__(self, originalModulePath: Path, fs: TempFileSystem,
                 parameterInfo: Const.ParamInfoList,
                 returnInfo: Const.ReturnInfoType,
                 *args, name: str = "", **kwargs):
        self.originalModulePath = originalModulePath
        self.fs = fs
        self.parameterInfo = parameterInfo
        self.returnInfo = returnInfo
        self.prepared = False
        self.modulePath: Const.OptionalPath = None  # Execution Priority #2
        self.executable: Const.OptionalPath = None  # Execution Priority #1
        self.name = name

    @classmethod
    def generateCompilationArgs(cls, *args, **kwargs) -> Const.ArgType:
        """
        Generate arguments to compile.
        """
        raise NotImplementedError

    @classmethod
    def generateExecutionArgs(cls, *args, **kwargs) -> Const.ArgType:
        """
        Generate arguments to invoke.
        """
        raise NotImplementedError

    @staticmethod
    def replaceSymbols(sourceCodePath: Path, mapping: dict) -> str:
        """
        Read sourcecode and replace symbols by mapping.
        """
        with open(sourceCodePath, "r") as sourceCodeFile:
            template = StringTemplate(sourceCodeFile.read())
        return template.substitute(mapping)

    @staticmethod
    def invoke(
            args: Const.ArgType, stdin: Path = None, stderr: Path = None,
            timelimit: float = Const.DefaultTimeLimit,
            memorylimit: float = Const.DefaultMemoryLimit,
            cwd: Path = None) -> Const.ExitCode:
        """
        Invoke given args with given stdin, stderr, timelimit and cwd.
        Note that stdin and stderr should be either None or existing file's path.
        Otherwise, it will be `DEVNULL`.
        """

        # Open stdin and stderr, and go
        stdin = open(stdin, "r") \
            if isExistingFile(stdin) else DEVNULL
        stderr = open(stderr, "w") \
            if isExistingFile(stderr) else DEVNULL
        result = Const.ExitCode.GeneralUnintendedFail

        # Make everything to be an absolute path
        for i in range(len(args)):
            if isinstance(args[i], Path):
                args[i] = args[i].absolute()

        # Execute
        try:
            P = Popen(
                args, stdin=stdin, stdout=DEVNULL, stderr=stderr,
                cwd=cwd, encoding='ascii',
                preexec_fn=limitSubprocessResource(timelimit, memorylimit))
            exitcode = P.wait(60)  # One minute for max
            for ec in Const.ExitCode:
                if ec.value == exitcode or ec.value + 256 == exitcode:
                    result = ec
                    break
        except TimeoutExpired:  # Something went wrong.
            result = Const.ExitCode.Killed
            P.kill()
        finally:  # Close file objects
            logger.debug("Executed \"%s\" with TL = %ds, ML = %gMB",
                         P.args, timelimit, memorylimit)
            if stdin != DEVNULL:
                stdin.close()
            if stderr != DEVNULL:
                stderr.close()

        # Return exitcode
        return result

    @classmethod
    def generateCode(cls, *args, **kwargs) -> str:
        """
        The most abstract method of `generateCode`.
        Read each child class's abstract method for details.
        """
        raise NotImplementedError

    def preparePipeline(self) -> None:
        """
        The most abstract method of `preparePipeline`.
        Read each child class's abstract method for details.
        At the end of this method, `self.prepared` should be set to True.
        """
        raise NotImplementedError

    def run(self, *args, **kwargs) -> Const.EXOO:
        """
        The most abstract method of `run`.
        This method should return `(ExitCode, outfile, stderr)`.
        Read each child class's abstract method for details.
        """
        raise NotImplementedError


class AbstractExternalGenerator(AbstractExternalModule):
    """
    Abstract base of Generator module.
    Generates the input data and print it to outfile.
    `func generate(args)` should be provided in original file.

    - argv: `[outfile, *genscript_args]`
    - stdin: None
    - Code structure: Preprocess -> Execution -> Print Out -> Postprocess
    """

    @classmethod
    def generateExecutionArgs(
            cls, outfile: typing.Union[str, Path], genscript: typing.List[str],
            modulePath: typing.Union[str, Path], *args, **kwargs) -> Const.ArgType:
        return [Path(modulePath), Path(outfile)] + genscript

    @classmethod
    def generateCode(cls, generatorPath: Path,
                     parameterInfo: Const.ParamInfoList,
                     *args, **kwargs) -> str:
        """
        Generate the generator code.
        """
        raise NotImplementedError

    def run(self, genscript: typing.List[str], *args, **kwargs) -> Const.EXOO:
        """
        Run generator with given genscript.
        Return exit code of generator subprocess and file path
        created in `self.fs` which contains generated input data.
        """
        if not self.prepared:
            raise AzadError("Generator not prepared")
        outfilePath = self.fs.newTempFile(extension="data", namePrefix="in")
        args = self.generateExecutionArgs(
            outfilePath, genscript,
            self.executable if self.executable else self.modulePath)
        errorLog = self.fs.newTempFile(extension="log", namePrefix="err")
        exitcode = self.invoke(args, stderr=errorLog,
                               timelimit=Const.DefaultGeneratorTL, **kwargs)
        return (exitcode, outfilePath, errorLog)


class AbstractExternalValidator(AbstractExternalModule):
    """
    Abstract base of Validator module.
    Validates the input data(generated by Generator) read from stdin.
    `func validate(param1, param2, ...)` should be provided in original file.

    - argv: `[]`
    """

    @classmethod
    def generateExecutionArgs(cls, modulePath: typing.Union[str, Path],
                              *args, **kwargs) -> Const.ArgType:
        return [Path(modulePath)]

    @classmethod
    def generateCode(
            cls, validatorPath: Path, parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType, *args, **kwargs) -> str:
        """
        Generate the validator code.
        """
        raise NotImplementedError

    def run(self, infile: Path, *args, **kwargs) -> Const.EXOO:
        """
        Run validator with given infile path.
        Return exit code of validator subprocess.
        """
        if not self.prepared:
            self.preparePipeline()
        args = self.generateExecutionArgs(
            self.executable if self.executable else self.modulePath)
        errorLog = self.fs.newTempFile(extension="log", namePrefix="err")
        exitcode = self.invoke(args, stdin=infile, stderr=errorLog,
                               timelimit=Const.DefaultValidatorTL, **kwargs)
        return (exitcode, None, errorLog)


class AbstractExternalSolution(AbstractExternalModule):
    """
    Abstract base of Solution module.

    - argv: `[outfile]`
    """

    @classmethod
    def generateExecutionArgs(
            cls, outfile: Path, modulePath: typing.Union[str, Path],
            *args, **kwargs) -> Const.ArgType:
        return [Path(modulePath), Path(outfile)]

    @classmethod
    def generateCode(
            cls, solutionPath: Path, parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType, *args, **kwargs) -> str:
        """
        Generate the solution code.
        """
        raise NotImplementedError

    def run(self, infile: Path, *args, **kwargs) -> Const.EXOO:
        """
        Run solution with given inflie path.
        Return exit code of solution process and file path
        created in `self.fs` which contains output data.
        """
        if not self.prepared:
            raise OSError("Generator not prepared")
        outfilePath = self.fs.newTempFile(extension="data", namePrefix="out")
        args = self.generateExecutionArgs(
            outfilePath, self.executable if self.executable else self.modulePath)
        errorLog = self.fs.newTempFile(extension="log", namePrefix="err")
        exitcode = self.invoke(args, stdin=infile, stderr=errorLog, **kwargs)
        return (exitcode, outfilePath, errorLog)
