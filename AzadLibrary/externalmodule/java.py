"""
This module provides implementation of Java external module.
"""

# Standard libraries
import typing
from pathlib import Path

# Azad libraries
from .. import constants as Const
from ..misc import isExistingFile, removeExtension, reportCompilationFailure
from ..errors import AzadError
from .abstract import (
    AbstractProgrammingLanguage, AbstractExternalGenerator,
    AbstractExternalValidator, AbstractExternalSolution)


class AbstractJava(AbstractProgrammingLanguage):
    """
    Java specification of abstract programming language.
    """

    baseTypeStrTable = {
        Const.IOVariableTypes.INT: "int",
        Const.IOVariableTypes.LONG: "long",
        Const.IOVariableTypes.FLOAT: "float",
        Const.IOVariableTypes.DOUBLE: "double",
        Const.IOVariableTypes.BOOL: "boolean",
        Const.IOVariableTypes.STRING: "String"
    }

    @classmethod
    def typeStr(cls, iovt: Const.IOVariableTypes, dimension: int):
        return cls.baseTypeStrTable[iovt] + ("[]" * dimension)

    # Template file path
    solutionTemplatePath = Const.ResourcesPath / "templates/solution_java.template"
    ioHelperTemplatePath = Const.ResourcesPath / "helpers/tchio.java"

    # Indent level
    indentLevelInitParameter = 2
    indentLevelGetParameter = 2

    @classmethod
    def templateDict(
            cls, *args,
            parameterInfo: typing.List[typing.Tuple[
                str, Const.IOVariableTypes, int]] = (),
            returnInfo: Const.ReturnInfoType = None,
            **kwargs) -> dict:

        # Language-common state
        result = super().templateDict(**kwargs)

        # Parameter arguments
        result["SendParameters"] = ", ".join(
            cls.vnameByPname(pName) for pName, _1, _2 in parameterInfo)

        # Init all parameters
        result["InitParameters"] = cls.leveledNewline(cls.indentLevelInitParameter).join(
            cls.generateCodeInitParameter(*param) for param in parameterInfo)

        # Get all parameters (for validator and solutions)
        result["GetParameters"] = cls.leveledNewline(cls.indentLevelGetParameter).join(
            cls.generateCodeGetParameter(*param) for param in parameterInfo)

        # Result info
        if returnInfo:
            returnType, returnDimension = returnInfo
            result["ReturnType"] = cls.typeStr(returnType, returnDimension)
            result["ReturnDimension"] = returnDimension

        # Return
        return result

    @classmethod
    def generateCodeInitParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        return "%s %s;" % \
            (cls.typeStr(parameterType, parameterDimension),
             cls.vnameByPname(variableName))

    @classmethod
    def generateCodeGetParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        return "%s = tchio.get%dd%s(sc);" % \
            (cls.vnameByPname(variableName), parameterDimension,
             cls.typeStr(parameterType, 0))


class JavaSolution(AbstractExternalSolution, AbstractJava):
    """
    Java implementation of external solution module.

    - argv:
        - Compilation: `['javac', mainModule, ioHelperModule]`
        - Execution: `['java', 'solution_java', *super().argv]`
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ioHelperModulePath = self.fs.copyFile(
            self.ioHelperTemplatePath, destName="tchio",
            extension="java", basePath=self.basePath)

    @classmethod
    def generateCode(
            cls, parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType,
            *args, **kwargs) -> str:
        return cls.replaceSymbols(
            cls.solutionTemplatePath, cls.templateDict(
                parameterInfo=parameterInfo,
                returnInfo=returnInfo)
        )

    @classmethod
    def generateCompilationArgs(
            cls, mainModule: Path, originalModule: Path,
            ioHelperModule: Path, *args, **kwargs):
        return ['javac', mainModule, originalModule, ioHelperModule]

    @classmethod
    def generateExecutionArgs(cls, outfile: Path, *args, **kwargs):
        return ['java', 'solution_java', outfile]

    def preparePipeline(self):
        if self.prepared:
            raise AzadError("Already prepared")

        # Replace original
        newOriginal = self.fs.copyFile(
            self.originalSourceCodePath, destName="Solution",
            extension="java", basePath=self.basePath)
        self.fs.pop(self.originalSourceCodePath)
        self.originalSourceCodePath = newOriginal

        # Prepare main body
        code = self.generateCode(self.parameterInfo, self.returnInfo)
        self.modulePath = self.fs.newTempFile(
            content=code, name="solution_java",
            extension="java", basePath=self.basePath)

        # Compile
        compilationArgs = self.generateCompilationArgs(
            self.modulePath, self.originalSourceCodePath, self.ioHelperModulePath)
        compilationErrorLog = self.newTempFile(
            extension="log", namePrefix="err")
        compilationExitCode = self.invoke(
            compilationArgs, stderr=compilationErrorLog, cwd=self.basePath)
        if compilationExitCode is not Const.ExitCode.Success:
            reportCompilationFailure(
                compilationErrorLog, self.modulePath,
                compilationArgs, Const.SourceFileType.Solution)

        self.prepared = True

    @staticmethod
    def invoke(*args, **kwargs) -> Const.ExitCode:
        return super(JavaSolution, JavaSolution).invoke(
            *args, memorylimit=2**20, **kwargs)
