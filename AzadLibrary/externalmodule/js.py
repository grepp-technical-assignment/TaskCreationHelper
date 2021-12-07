"""
This module provides implementation of Javascript external module.
"""

# Standard libraries
import typing
from pathlib import Path

# Azad libraries
from .. import constants as Const
from ..misc import isExistingFile, removeExtension, reportCompilationFailure
from ..errors import AzadError
from .abstract import (
    AbstractProgrammingLanguage,
    AbstractExternalSolution
)

class AbstractJs(AbstractProgrammingLanguage):
    """
    Javascript specification of abstract programming language.
    """

    # baseTypeStrTable = {
    #     Const.IOVariableTypes.INT: "int",
    #     Const.IOVariableTypes.LONG: "long",
    #     Const.IOVariableTypes.FLOAT: "float",
    #     Const.IOVariableTypes.DOUBLE: "double",
    #     Const.IOVariableTypes.BOOL: "boolean",
    #     Const.IOVariableTypes.STRING: "String"
    # }

    # Template file path
    solutionTemplatePath = Const.ResourcesPath / "templates/solution_javascript.template"
    ioHelperTemplatePath = Const.ResourcesPath / "helpers/tchio.js"

    # Indent level
    indentLevelInitParameter = 1
    indentLevelGetParameter = 2

    @classmethod
    def templateDict(cls,
        *args,
        parameterInfo: typing.List[typing.Tuple[str, Const.IOVariableTypes, int]] = (),
        ioHelperPath: Path = None,
        solutionPath: Path = None,
        returnInfo: Const.ReturnInfoType = None,
        **kwargs,
    ) -> dict:
        """
        Return dictionary to replace generated code.
        Be aware that some arguments passed by `kwargs`
        may be replaced in child class method.

         * JsIOHelperPath: tchio module path
         * SolutionPath: solution path
         * InitParameters: init parameters
         * GetParameters: get parameters
         * ExitCodeInputParsingError: exit code when input parsing error
         * ExitCodeSolutionFailed: exit code when runtime error
         * ExitCodeWrongTypeGenerated: exit code when output error
         * ExitCodeSuccess: exit code when success
         * ReturnType: return type
         * ReturnDimension: return dimension
         * Parameters: parameters name
        """
        result = super().templateDict(**kwargs)

        def registerPath(key: str, path: Path):
            if path:
                if not isExistingFile(path):
                    raise OSError(
                        "Given path(key = %s, path = %s) isn't existing file" % (key, path)
                    )
                result[key] = path

        # Set paths
        registerPath("JsIOHelperPath", ioHelperPath)
        registerPath("SolutionPath", solutionPath)

        # Init parameters
        result["InitParameters"] = cls.leveledNewline(cls.indentLevelInitParameter).join(
            cls.generateCodeInitParameter(*param) for param in parameterInfo
        )
        # Get parameters
        result["GetParameters"] = cls.leveledNewline(cls.indentLevelGetParameter).join(
            cls.generateCodeGetParameter(*param) for param in parameterInfo
        )

        # Return info
        if returnInfo:
            returnType, returnDimension = returnInfo
            result["ReturnType"] = "\"%s\"" % (returnType.value,)
            result["ReturnDimension"] = returnDimension

        # Parameters
        result["Parameters"] = ", ".join(param[0] for param in parameterInfo)
        return result

    @classmethod
    def generateCodeInitParameter(cls,
        variableName: str,
        parameterType: Const.IOVariableTypes,
        parameterDimension: int
    ) -> str:
        """
        Return statement `pType varName;`
        """
        return "var %s;" % (variableName,)

    @classmethod
    def generateCodeGetParameter(cls,
        variableName: str,
        parameterType: Const.IOVariableTypes,
        parameterDimension: int
    ) -> str:
        """
        Return statement `$Param = TCHIO.parse(input, $ParamType, $ParamDimension);`.
        """
        return "%s = TCHIO.parse(input, \"%s\", %d);" \
            % (variableName, parameterType.value, parameterDimension)

class JsSolution(AbstractExternalSolution, AbstractJs):
    """
    Javascript implementation of external solution module.

    - argv:
        - Execution: `['node', 'solution_js', *super().argv]`
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ioHelperPath = self.fs.copyFile(
            self.ioHelperTemplatePath, destName="tchio",
            extension="js", basePath=self.basePath
        )
        self.solutionPath = self.fs.copyFile(
            self.solutionTemplatePath, destName="solution_javascript_template",
            extension="js", basePath=self.basePath
        )

    @classmethod
    def generateCode(cls,
        parameterInfo: Const.ParamInfoList,
        returnInfo: Const.ReturnInfoType,
        solutionPath: Path,
        ioHelperPath: Path,
        *args, **kwargs
    ) -> str:
        return cls.replaceSymbols(
            cls.solutionTemplatePath,
            cls.templateDict(
                parameterInfo=parameterInfo,
                returnInfo=returnInfo,
                solutionPath=solutionPath,
                ioHelperPath=ioHelperPath,
            )
        )

    @classmethod
    def generateExecutionArgs(cls, outfile: Path, *args, **kwargs):
        return ['node', 'solution_js', outfile]

    def preparePipeline(self):
        if self.prepared:
            raise AzadError("Already prepared")
        # Prepare main body
        code = self.generateCode(
            self.parameterInfo, self.returnInfo,
            self.solutionPath, self.ioHelperPath,
        )
        self.modulePath = self.fs.newTempFile(
            content=code, name="solution_js",
            extension="js", basePath=self.basePath
        )
        self.prepared = True

    # @staticmethod
    # def invoke(*args, **kwargs) -> Const.ExitCode:
    #     if "memorylimit" in kwargs:
    #         del kwargs["memorylimit"]
    #     return super(JsSolution, JsSolution).invoke(
    #         *args, memorylimit=2**20, **kwargs)