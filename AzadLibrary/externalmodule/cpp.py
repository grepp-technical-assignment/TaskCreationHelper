"""
This module provides implementation of C++ external module.
"""

# Standard libraries
import typing
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Azad libraries
from .. import constants as Const
from ..misc import isExistingFile, removeExtension, formatPathForLog
from ..errors import AzadError
from .abstract import (
    AbstractProgrammingLanguage, AbstractExternalGenerator,
    AbstractExternalValidator, AbstractExternalSolution)


def reportCompilationFailure(
        errLogPath: Path, modulePath: Path,
        args: typing.List[typing.Union[str, Path]],
        moduleType: Const.SourceFileType):
    """
    Report C/C++ compilation failure.
    """
    newArgs = [formatPathForLog(arg) if isinstance(arg, Path)
               else arg for arg in args]
    with open(errLogPath, "r") as errLogFile:
        logger.error(
            "Compilation failure on %s \"%s\"; args = %s, log =\n%s",
            moduleType.name, formatPathForLog(modulePath),
            newArgs, errLogFile.read())
        raise AzadError(
            "Compilation failure on %s \"%s\"; args = %s" %
            (moduleType.name, formatPathForLog(modulePath), newArgs))


class AbstractCpp(AbstractProgrammingLanguage):
    """
    C++ specification of abstract programming language.
    """

    baseTypeStrTable = {
        Const.IOVariableTypes.INT: "int",
        Const.IOVariableTypes.LONG: "long long int",
        Const.IOVariableTypes.FLOAT: "float",
        Const.IOVariableTypes.DOUBLE: "double",
        Const.IOVariableTypes.BOOL: "bool",
        Const.IOVariableTypes.STRING: "std::string"
    }

    @classmethod
    def typeStr(cls, iovt: Const.IOVariableTypes, dimension: int):
        return cls.baseTypeStrTable[iovt] if dimension == 0 else \
            "std::vector<%s>" % cls.typeStr(iovt, dimension - 1)

    # Template file path
    generatorTemplatePath = Const.ResourcesPath / \
        "templates/generator_cpp.template"
    solutionTemplatePath = Const.ResourcesPath / \
        "templates/solution_cpp.template"
    validatorTemplatePath = Const.ResourcesPath / \
        "templates/validator_cpp.template"
    helperHeadersPath = Const.ResourcesPath / "helpers"

    # Indent level
    indentLevelParameterInit = 1
    indentLevelParameterGet = 2
    indentLevelParameterPrint = 2

    # Converted variable name on C++ code
    vnameByPname = (lambda name: "_param_%s" % (name,))

    @classmethod
    def templateDict(
            cls, *args, parameterInfo: typing.List[typing.Tuple[
                str, Const.IOVariableTypes, int]] = (),
            returnInfo: Const.ReturnInfoType = None,
            **kwargs) -> dict:

        # Language-common state
        result = super().templateDict(**kwargs)

        # Parameter arguments (for all modules)
        result["ParameterArgs"] = ", ".join(
            "%s %s" % (cls.typeStr(pType, dimension), pName)
            for pName, pType, dimension in parameterInfo)
        result["ParameterArgsRef"] = ", ".join(
            "%s &%s" % (cls.typeStr(pType, dimension), pName)
            for pName, pType, dimension in parameterInfo)
        result["SendParameters"] = ", ".join(
            cls.vnameByPname(pName) for pName, _1, _2 in parameterInfo)

        # Init all parameters (for all modules)
        result["InitParameters"] = cls.leveledNewline(cls.indentLevelParameterInit).join(
            cls.generateCodeInitParameter(*param) for param in parameterInfo)

        # Get all parameters (for validators and solutions)
        result["GetParameters"] = cls.leveledNewline(cls.indentLevelParameterGet).join(
            cls.generateCodeGetParameter(*param) for param in parameterInfo)

        # Print all parameters (for generators)
        result["PrintParameters"] = cls.leveledNewline(cls.indentLevelParameterPrint).join(
            cls.generateCodePutParameter(*param) for param in parameterInfo)

        # Result info
        if returnInfo:
            returnType, returnDimension = returnInfo
            result["ReturnType"] = cls.typeStr(returnType, returnDimension)
            result["ReturnDimension"] = returnDimension
            result["ReturnTypeBase"] = cls.typeStr(returnType, 0)

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
        return "%s = TCH::Data<%s, %d>::get(std::cin);" % \
            (cls.vnameByPname(variableName),
             cls.typeStr(parameterType, 0),
             parameterDimension)

    @classmethod
    def generateCodePutParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        return "TCH::Data<%s, %d>::put(outfile, %s);" % \
            (cls.typeStr(parameterType, 0),
             parameterDimension,
             cls.vnameByPname(variableName))


class CppGenerator(AbstractExternalGenerator, AbstractCpp):
    """
    C++ implementation of external generator module.
    `generateExecutionArgs` is not overrided, because in C++
    we invokes executable created by compilation.

    - argv: `[executable, *super().argv]`
    """

    @classmethod
    def generateCompilationArgs(
            cls, mainModulePath: Path, executable: Path,
            originalModulePath: Path, *args, **kwargs) -> Const.ArgType:
        return [
            "g++", "-Wall", "-std=c++17", "-O2",
            "-I", cls.helperHeadersPath,
            mainModulePath, originalModulePath,
            "-o", executable
        ]

    @classmethod
    def generateCode(
            cls, parameterInfo: Const.ParamInfoList,
            *args, **kwargs) -> str:
        """
        Consider `generatorPath` as `generatorHeaderPath`.
        """
        return cls.replaceSymbols(
            cls.generatorTemplatePath,
            cls.templateDict(parameterInfo=parameterInfo)
        )

    def preparePipeline(self):

        # Prepare original stuffs
        code = self.generateCode(self.parameterInfo)
        self.modulePath = self.fs.newTempFile(
            content=code, extension="cpp", namePrefix="generator")

        # Compile
        self.executable = self.fs.newTempFile(
            extension="exe", namePrefix="generator")
        compilationArgs = self.generateCompilationArgs(
            self.modulePath, self.executable, self.originalModulePath)
        compilationErrorLog = self.fs.newTempFile(
            extension="log", namePrefix="err")
        compilationExitCode = self.invoke(
            compilationArgs, stderr=compilationErrorLog,
            cwd=self.fs.basePath)
        if compilationExitCode is not Const.ExitCode.Success:
            reportCompilationFailure(
                compilationErrorLog, self.originalModulePath,
                compilationArgs, Const.SourceFileType.Generator)

        self.prepared = True


class CppValidator(AbstractExternalValidator, AbstractCpp):
    """
    C++ implementation of external validator module.
    `generateExecutionArgs` is not overrided, because in C++
    we invokes executable created by compilation.

    - argv: `[executable, *super().argv]`
    """

    @classmethod
    def generateCompilationArgs(
            cls, mainModulePath: Path, executable: Path,
            originalModulePath: Path, *args, **kwargs) -> Const.ArgType:
        return [
            "g++", "-Wall", "-std=c++17", "-O2",
            "-I", cls.helperHeadersPath,
            mainModulePath, originalModulePath,
            "-o", executable
        ]

    @classmethod
    def generateCode(
            cls, parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType,
            *args, **kwargs) -> str:
        """
        Consider `validatorPath` as `validatorHeaderPath`.
        """
        return cls.replaceSymbols(
            cls.validatorTemplatePath,
            cls.templateDict(
                parameterInfo=parameterInfo,
                returnInfo=returnInfo)
        )

    def preparePipeline(self):

        # Prepare original stuffs
        code = self.generateCode(self.parameterInfo, self.returnInfo)
        self.modulePath = self.fs.newTempFile(
            content=code, extension="cpp", namePrefix="validator")

        # Compile
        self.executable = self.fs.newTempFile(
            extension="exe", namePrefix="validator")
        compilationArgs = self.generateCompilationArgs(
            self.modulePath, self.executable, self.originalModulePath)
        compilationErrorLog = self.fs.newTempFile(
            extension="log", namePrefix="err")
        compilationExitCode = self.invoke(
            compilationArgs, stderr=compilationErrorLog,
            cwd=self.fs.basePath)
        if compilationExitCode is not Const.ExitCode.Success:
            reportCompilationFailure(
                compilationErrorLog, self.originalModulePath,
                compilationArgs, Const.SourceFileType.Validator)

        self.prepared = True


class CppSolution(AbstractExternalSolution, AbstractCpp):
    """
    C++ implementation of external solution module.
    `generateExecutionArgs` is not overrided, because in C++
    we invokes executable created by compilation.

    - argv: `[executable, *super().argv]`
    """

    @classmethod
    def generateCompilationArgs(
            cls, mainModulePath: Path, executable: Path,
            originalModulePath: Path, *args, **kwargs) -> Const.ArgType:
        return [
            "g++", "-Wall", "-std=c++17", "-O2",
            "-I", cls.helperHeadersPath,
            mainModulePath, originalModulePath,
            "-o", executable
        ]

    @classmethod
    def generateCode(
            cls, parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType,
            *args, **kwargs) -> str:
        """
        Consider `solutionPath` as `solutionHeaderPath`.
        """
        return cls.replaceSymbols(
            cls.solutionTemplatePath,
            cls.templateDict(
                parameterInfo=parameterInfo,
                returnInfo=returnInfo)
        )

    def preparePipeline(self):

        # Prepare original stuffs
        code = self.generateCode(self.parameterInfo, self.returnInfo)
        self.modulePath = self.fs.newTempFile(
            content=code, extension="cpp", namePrefix="solution")

        # Compile
        self.executable = self.fs.newTempFile(
            extension="exe", namePrefix="solution")
        compilationArgs = self.generateCompilationArgs(
            self.modulePath, self.executable,
            self.originalModulePath)
        compilationErrorLog = self.fs.newTempFile(
            extension="log", namePrefix="err")
        compilationExitCode = self.invoke(
            compilationArgs, stderr=compilationErrorLog,
            cwd=self.fs.basePath)
        if compilationExitCode is not Const.ExitCode.Success:
            reportCompilationFailure(
                compilationErrorLog, self.originalModulePath,
                compilationArgs, Const.SourceFileType.Solution)

        self.prepared = True


class AbstractC(AbstractCpp):
    """
    C++ specification of abstract programming language.
    """

    baseTypeStrTable = {
        Const.IOVariableTypes.INT: "int",
        Const.IOVariableTypes.LONG: "long long int",
        Const.IOVariableTypes.FLOAT: "float",
        Const.IOVariableTypes.DOUBLE: "double",
        Const.IOVariableTypes.BOOL: "bool",
        Const.IOVariableTypes.STRING: "char*"
    }

    @classmethod
    def typeStr(cls, iovt: Const.IOVariableTypes, dimension: int):
        return cls.baseTypeStrTable[iovt] + "*" * dimension

    # Template file path
    solutionTemplatePath = Const.ResourcesPath / \
        "templates/solution_c.template"

    # Indent level
    indentLevelParameterInit = 1
    indentLevelParameterGet = 2
    indentLevelParameterPrint = 2
    indentLevelParameterFree = 2
    indentLevelParameterConvertCppC = 2

    # Converted variable name on C++ code
    vnameByPname = (lambda name: "_param_clang_%s" % (name,))

    @classmethod
    def templateDict(
            cls, *args, parameterInfo: typing.List[typing.Tuple[
                str, Const.IOVariableTypes, int]] = (),
            returnInfo: Const.ReturnInfoType = None,
            **kwargs) -> dict:

        # Language-common state
        result = super().templateDict(**kwargs)

        # Parameter arguments (for all modules)
        result["ParameterArgs"] = ", ".join(
            "%s %s" % (cls.typeStr(pType, dimension), pName)
            for pName, pType, dimension in parameterInfo)
        result["SendParameters"] = ", ".join(
            cls.vnameByPname(pName) for pName, _1, _2 in parameterInfo)

        # Init all parameters (for all modules)
        result["InitCppParameters"] = cls.leveledNewline(
            cls.indentLevelParameterInit).join(
            cls.generateCodeInitParameter(*param, clang=False)
                for param in parameterInfo)
        result["InitCParameters"] = cls.leveledNewline(
            cls.indentLevelParameterInit).join(
            cls.generateCodeInitParameter(*param, clang=True)
                for param in parameterInfo)

        # Get all parameters (for validators and solutions)
        result["GetCppParameters"] = cls.leveledNewline(
            cls.indentLevelParameterGet).join(
            AbstractCpp.generateCodeGetParameter(*param)
                for param in parameterInfo)

        # Free parameters (for all modules)
        result["FreeCParameters"] = cls.leveledNewline(
            cls.indentLevelParameterFree).join(
            cls.generateCodeFreeParameter(*param)
                for param in parameterInfo)

        # Convert parameters Cpp -> C (for all modules)
        result["ConvertParametersCppC"] = cls.leveledNewline(
            cls.indentLevelParameterConvertCppC).join(
            cls.generateCodeConvertParameter(*param, True)
                for param in parameterInfo)

        # Result info
        if returnInfo:
            returnType, returnDimension = returnInfo
            result["ReturnCppType"] = \
                AbstractCpp.typeStr(returnType, returnDimension)
            result["ReturnCType"] = cls.typeStr(returnType, returnDimension)
            result["ReturnDimension"] = returnDimension
            result["ReturnTypeBase"] = cls.typeStr(returnType, 0)
            result["ReturnTypeBaseCpp"] = AbstractCpp.typeStr(returnType, 0)

        # Return
        return result

    @ classmethod
    def generateCodeInitParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int,
            clang: bool = True) -> str:
        return "%s %s;" % \
            (cls.typeStr(parameterType, parameterDimension),
             (cls if clang else super()).vnameByPname(variableName))

    @ classmethod
    def generateCodeGetParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        return "%s = TCH::Data<%s, %d>::get(std::cin);" % \
            (super().vnameByPname(variableName),
             super().typeStr(parameterType, 0),
             parameterDimension)

    @ classmethod
    def generateCodeFreeParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        return "TCH::Data<%s, %d>::superfree(%s);" % \
            (super().typeStr(parameterType, 0),
             parameterDimension,
             cls.vnameByPname(variableName))

    @ classmethod
    def generateCodeConvertParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int,
            fromCpp: bool) -> str:
        middle: str = "TCH::Data<%s, %d>" % \
            (super().typeStr(parameterType, 0),
             parameterDimension)
        nameC: str = cls.vnameByPname(variableName)
        nameCpp: str = super().vnameByPname(variableName)
        if fromCpp:  # C++ -> C
            return "%s = %s::convert_%s(%s);" % \
                (nameC, middle, "cpp_c", nameCpp)
        else:  # C -> C++
            return "%s = %s::convert_%s(%s);" % \
                (nameCpp, middle, "c_cpp", nameC)


class CSolution(AbstractExternalSolution, AbstractC):
    """
    C implementation of external solution module.

    - argv: `[executable, *super().argv]`
    """

    @classmethod
    def generateCode(
            cls, parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType,
            *args, **kwargs) -> str:
        """
        Consider `solutionPath` as `solutionHeaderPath`.
        """
        return cls.replaceSymbols(
            cls.solutionTemplatePath,
            cls.templateDict(
                parameterInfo=parameterInfo,
                returnInfo=returnInfo)
        )

    def preparePipeline(self):

        # Prepare original stuffs
        code = self.generateCode(self.parameterInfo, self.returnInfo)
        self.modulePath = self.fs.newTempFile(
            content=code, extension="cpp", namePrefix="solution")

        # Compile: C
        executableTempC = self.fs.newTempFile(
            extension="exe", namePrefix="solution")
        compilationArgs1 = [
            "gcc", "-c", self.originalModulePath,
            "-std=c11", "-O2", "-Wall",
            "-I", self.helperHeadersPath,
            "-o", executableTempC]
        compilationErrorLog1 = self.fs.newTempFile(
            extension="log", namePrefix="err")
        compilationExitCode1 = self.invoke(
            compilationArgs1, stderr=compilationErrorLog1,
            cwd=self.fs.basePath)

        # If failed to compile C?
        if compilationExitCode1 is not Const.ExitCode.Success:
            reportCompilationFailure(
                compilationErrorLog1, self.originalModulePath,
                compilationArgs1, Const.SourceFileType.Solution)

        # Compile: C++
        executableTempCpp = self.fs.newTempFile(
            extension="exe", namePrefix="solution")
        compilationArgs2 = [
            "g++", "-c", self.modulePath,
            "-std=c++17", "-O2", "-Wall",
            "-I", self.helperHeadersPath,
            "-o", executableTempCpp
        ]
        compilationErrorLog2 = self.fs.newTempFile(
            extension="log", namePrefix="err")
        compilationExitCode2 = self.invoke(
            compilationArgs2, stderr=compilationErrorLog2,
            cwd=self.fs.basePath)

        # If failed to compile C++?
        if compilationExitCode2 is not Const.ExitCode.Success:
            reportCompilationFailure(
                compilationErrorLog2, self.modulePath,
                compilationArgs2, Const.SourceFileType.Solution)

        # Compile: Together
        self.executable = self.fs.newTempFile(
            extension="exe", namePrefix="solution")
        compilationArgs3 = [
            "g++", executableTempC, executableTempCpp,
            "-o", self.executable
        ]
        compilationErrorLog3 = self.fs.newTempFile(
            extension="log", namePrefix="err")
        compilationExitCode3 = self.invoke(
            compilationArgs3, stderr=compilationErrorLog3,
            cwd=self.fs.basePath)

        # If failed last step?
        if compilationExitCode3 is not Const.ExitCode.Success:
            reportCompilationFailure(
                compilationErrorLog3, executableTempCpp,
                compilationArgs3, Const.SourceFileType.Solution)

        # Clean useless binary files
        self.fs.pop(executableTempC, b=True)
        self.fs.pop(executableTempCpp, b=True)
        self.prepared = True
