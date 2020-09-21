"""
This module provides abstract base interface of code generator.
"""

# Standard libraries
import typing
from pathlib import Path
from subprocess import Popen, DEVNULL, TimeoutExpired
from string import Template as StringTemplate

# Azad libraries
from .. import constants as Const
from ..filesystem import TempFileSystem
from ..misc import isExistingFile

# Short name of type hints
OptionalPath = typing.Union[Path, None]
EXOO = typing.Tuple[Const.ExitCode, OptionalPath,
                    OptionalPath]  # (ExitCode, outfile, stderr)
ArgType = typing.List[typing.Union[str, Path]]
ParamInfoSingle = typing.Tuple[str, Const.IOVariableTypes, int]
ParamInfoList = typing.List[ParamInfoSingle]
ReturnInfoType = typing.Tuple[Const.IOVariableTypes, int]


class AbstractProgrammingLanguage:
    """
    Abstract base of programming language for external module.
    """

    # Default indentation
    defaultIndentation = 4

    # typeStrTable[IOVT][dimension] is corresponding type in language.
    typeStrTable = {_iovt: [NotImplemented for _ in range(3)]
                    for _iovt in Const.IOVariableTypes}

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
    def templateDict(cls, **kwargs) -> dict:
        """
        Return dictionary to replace generated code.
        Be aware that some arguments passed by `kwargs`
        may be replaced in child class method.
        """
        result = {"ExitCode" + v.name: v.value
                  for v in Const.IOVariableTypes}
        result.update(**kwargs)
        return result


class AbstractExternalModule:
    """
    Abstract base of all external modules.
    When you inherit and make new modules, please inherit like
    `class NewLanguage$Filetype($AbstractFiletype, $AbstractLang): ...`.
    Stream `stdout` is set to `DEVNULL` in subprocess
    for all external modules and subprocesses for better performance.
    """

    def __init__(self, originalModulePath: Path, fs: TempFileSystem,
                 parameterInfo: ParamInfoList, returnInfo: ReturnInfoType):
        self.originalModulePath = originalModulePath
        self.fs = fs
        self.parameterInfo = parameterInfo
        self.returnInfo = returnInfo
        self.prepared = False
        self.modulePath: OptionalPath = None
        self.preparePipeline()

    @classmethod
    def generateArgs(cls, *args, **kwargs) -> ArgType:
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
            args: ArgType, stdin: Path = None, stderr: Path = None,
            timelimit: float = Const.DefaultTimeLimit,
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

        # Execute
        try:
            subprocess = Popen(
                args, stdin=stdin, stdout=DEVNULL, stderr=stderr,
                cwd=cwd, encoding='utf-8')
            exitcode = subprocess.wait(timelimit)
            for ec in Const.ExitCode:
                if ec.value == exitcode:
                    result = ec
                    break
        except TimeoutExpired:  # TLE
            result = Const.ExitCode.TLE
            subprocess.kill()
        finally:  # Close file objects
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

    def preparePipeline(self, *args, **kwargs) -> None:
        """
        The most abstract method of `preparePipeline`.
        Read each child class's abstract method for details.
        At the end of this method, `self.prepared` should be set to True.
        """
        raise NotImplementedError

    def run(self, *args, **kwargs) -> EXOO:
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
    def generateArgs(
            cls, outfile: typing.Union[str, Path], genscript: typing.List[str],
            modulePath: typing.Union[str, Path], *args, **kwargs) -> ArgType:
        return [Path(modulePath), Path(outfile)] + genscript

    @classmethod
    def generateCode(cls, generatorPath: Path, parameterInfo: ParamInfoList,
                     *args, **kwargs) -> str:
        """
        Generate the generator code.
        """
        raise NotImplementedError

    def run(self, genscript: typing.List[str], *args, **kwargs) -> EXOO:
        """
        Run generator with given genscript.
        Return exit code of generator subprocess and file path
        created in `self.fs` which contains generated input data.
        """
        if not self.prepared:
            raise OSError("Generator not prepared")
        outfilePath = self.fs.newTempFile(extension="out")
        args = self.generateArgs(outfilePath, genscript, self.modulePath)
        errorLog = self.fs.newTempFile(extension="log")
        exitcode = self.invoke(
            args, stderr=errorLog, timelimit=10.0, cwd=self.fs.basePath)
        return (exitcode, outfilePath, errorLog)


class AbstractExternalValidator(AbstractExternalModule):
    """
    Abstract base of Validator module.
    Validates the input data(generated by Generator) read from stdin.
    `func validate(param1, param2, ...)` should be provided in original file.

    - argv: `[]`
    """

    @classmethod
    def generateArgs(cls, modulePath: typing.Union[str, Path],
                     *args, **kwargs) -> ArgType:
        return [Path(modulePath)]

    @classmethod
    def generateCode(
            cls, validatorPath: Path, parameterInfo: ParamInfoList,
            returnInfo: ReturnInfoType, *args, **kwargs) -> str:
        """
        Generate the validator code.
        """
        raise NotImplementedError

    def run(self, infile: Path, *args, **kwargs) -> EXOO:
        """
        Run validator with given infile path.
        Return exit code of validator subprocess.
        """
        if not self.prepared:
            raise OSError("Generator not prepared")
        args = self.generateArgs(self.modulePath)
        errorLog = self.fs.newTempFile(extension="log")
        exitcode = self.invoke(args, stdin=infile, stderr=errorLog,
                               timelimit=10.0, cwd=self.fs.basePath)
        return (exitcode, None, errorLog)


class AbstractExternalSolution(AbstractExternalModule):
    """
    Abstract base of Solution module.

    - argv: `[outfile]`
    """

    @classmethod
    def generateArgs(
            cls, outfile: Path, modulePath: typing.Union[str, Path],
            *args, **kwargs) -> ArgType:
        return [Path(modulePath), Path(outfile)]

    @classmethod
    def generateCode(cls, solutionPath: Path, parameterInfo: ParamInfoList,
                     returnInfo: ReturnInfoType, *args, **kwargs) -> str:
        """
        Generate the solution code.
        """
        raise NotImplementedError

    def run(self, infile: Path, *args, **kwargs) -> EXOO:
        """
        Run solution with given inflie path.
        Return exit code of solution process and file path
        created in `self.fs` which contains output data.
        """
        if not self.prepared:
            raise OSError("Generator not prepared")
        outfilePath = self.fs.newTempFile(extension="out")
        args = self.generateArgs(outfilePath, self.modulePath)
        errorLog = self.fs.newTempFile(extension="log")
        exitcode = self.invoke(args, stdin=infile, stderr=errorLog,
                               timelimit=10.0, cwd=self.fs.basePath)
        return (exitcode, outfilePath, errorLog)
