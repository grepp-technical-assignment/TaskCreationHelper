"""
This module provides implementation of Python3 external module.
"""

# Standard libraries
import typing
from pathlib import Path

# Azad libraries
from .. import constants as Const
from ..misc import isExistingFile, removeExtension
from .abstract import (
    AbstractProgrammingLanguage, AbstractExternalGenerator,
    AbstractExternalValidator, AbstractExternalSolution)


class AbstractPython3(AbstractProgrammingLanguage):
    """
    Python3 specification of abstract programming language.
    """

    typeStrTable = {
        Const.IOVariableTypes.INT: [
            "int", "typing.List[int]", "typing.List[typing.List[int]]"],
        Const.IOVariableTypes.LONG: [
            "int", "typing.List[int]", "typing.List[typing.List[int]]"],
        Const.IOVariableTypes.FLOAT: [
            "float", "typing.List[float]", "typing.List[typing.List[float]]"],
        Const.IOVariableTypes.DOUBLE: [
            "float", "typing.List[float]", "typing.List[typing.List[float]]"],
        Const.IOVariableTypes.BOOL: [
            "bool", "typing.List[bool]", "typing.List[typing.List[bool]]"],
        Const.IOVariableTypes.STRING: [
            "str", "typing.List[str]", "typing.List[typing.List[str]]"]
    }

    # Template file path
    generatorTemplatePath = Const.ResourcesPath / \
        "templates/generator_python3.template"
    solutionTemplatePath = Const.ResourcesPath / \
        "templates/solution_python3.template"
    validatorTemplatePath = Const.ResourcesPath / \
        "templates/validator_python3.template"
    ioHelperTemplatePath = Const.ResourcesPath / "helpers/tchio.py"

    # Indent level
    getParameterIndentLevel = 2
    putParameterIndentLevel = 2

    @classmethod
    def templateDict(
            cls, parameterInfo: typing.List[typing.Tuple[
                str, Const.IOVariableTypes, int]] = (),
            generatorPath: Path = None, validatorPath: Path = None,
            solutionPath: Path = None, ioHelperPath: Path = None,
            returnInfo: Const.ReturnInfoType = None,
            **kwargs) -> dict:

        # Language-common state
        result = super().templateDict(**kwargs)

        # Get all parameters (for validator and solutions)
        result["GetParameters"] = cls.leveledNewline(cls.getParameterIndentLevel).join(
            cls.generateCodeGetParameter(*parameter) for parameter in parameterInfo)

        # Print all parameters (for generators)
        result["PrintParameters"] = cls.leveledNewline(cls.putParameterIndentLevel).join(
            cls.generateCodePutParameter(*parameter) for parameter in parameterInfo)

        # Result info
        if returnInfo:
            returnType, returnDimension = returnInfo
            result["ReturnType"] = cls.typeStrTable[returnType][0]
            result["ReturnDimension"] = returnDimension

        # Paths; At least one of these should be provided
        if not (isinstance(generatorPath, Path) or
                isinstance(validatorPath, Path) or
                isinstance(solutionPath, Path)):
            raise OSError(
                "None of Generator, Validator, Solution path are provided")

        def registerPath(key: str, path: Path, force: bool = False):
            if path or force:
                if not isExistingFile(path):
                    raise OSError(
                        "Given path(key = %s, path = %s) isn't existing file" %
                        (key, path))
                result[key] = removeExtension(path)

        registerPath("GeneratorPath", generatorPath)
        registerPath("ValidatorPath", validatorPath)
        registerPath("SolutionPath", solutionPath)
        registerPath("PythonIOHelperPath", ioHelperPath, force=True)

        # Return
        return result

    @classmethod
    def generateCodeGetParameter(
            cls, variableName: int,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        tReal = cls.typeStrTable[parameterType][0]
        tHint = cls.typeStrTable[parameterType][parameterDimension]
        return "inputValues['%s']: %s = TCHIO.parseMulti(inputLineIterator, %s, %d)" % \
            (variableName, tHint, tReal, parameterDimension)

    @classmethod
    def generateCodePutParameter(
            cls, variableName: int,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        tReal = cls.typeStrTable[parameterType][0]
        return "TCHIO.printData(generated['%s'], %s, %s, file = outfile); del generated['%s']" % \
            (variableName, tReal, parameterDimension, variableName)


class Python3Generator(AbstractExternalGenerator, AbstractPython3):
    """
    Python3 implementation of external generator module.

    - argv: `[python3, modulepath, *super().argv]`
    """

    # Indent level
    getParameterIndentLevel = 3
    putParameterIndentLevel = 3

    def __init__(self, *args, ioHelperModulePath: Path = None, **kwargs):
        self.ioHelperModulePath = ioHelperModulePath
        super().__init__(*args, **kwargs)

    @classmethod
    def generateArgs(cls, outfile: typing.Union[str, Path],
                     genscript: typing.List[str],
                     modulePath: typing.Union[str, Path],
                     *args, **kwargs) -> Const.ArgType:
        return ["python3", *super().generateArgs(
            outfile, genscript, modulePath, *args, **kwargs)]

    @classmethod
    def generateCode(
            cls, generatorPath: Path, parameterInfo: Const.ParamInfoList,
            ioHelperPath: Path, *args, **kwargs) -> str:
        return cls.replaceSymbols(
            cls.generatorTemplatePath, cls.templateDict(
                parameterInfo=parameterInfo,
                generatorPath=generatorPath, ioHelperPath=ioHelperPath,
                **kwargs)
        )

    def preparePipeline(self, *args, **kwargs):
        code = self.generateCode(
            self.originalModulePath, self.parameterInfo,
            self.ioHelperModulePath)
        self.modulePath = self.fs.newTempFile(
            code, extension=Const.SourceFileLanguage.Python3.value,
            namePrefix="generator")
        self.prepared = True


class Python3Validator(AbstractExternalValidator, AbstractPython3):
    """
    Python3 implementation of external validator module.

    - argv: `[python3, modulepath, *super().argv]`
    """

    def __init__(self, *args, ioHelperModulePath: Path = None, **kwargs):
        self.ioHelperModulePath = ioHelperModulePath
        super().__init__(*args, **kwargs)

    @classmethod
    def generateArgs(cls, modulePath: typing.Union[str, Path],
                     *args, **kwargs) -> Const.ArgType:
        return ["python3",
                *super().generateArgs(modulePath, *args, **kwargs)]

    @classmethod
    def generateCode(
            cls, validatorPath: Path, parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType, ioHelperPath: Path,
            *args, **kwargs) -> str:
        return cls.replaceSymbols(
            cls.validatorTemplatePath,
            cls.templateDict(
                parameterInfo=parameterInfo,
                validatorPath=validatorPath, ioHelperPath=ioHelperPath,
                **kwargs)
        )

    def preparePipeline(self, *args, **kwargs):
        code = self.generateCode(
            self.originalModulePath, self.parameterInfo,
            self.returnInfo, self.ioHelperModulePath)
        self.modulePath = self.fs.newTempFile(
            code, extension=Const.SourceFileLanguage.Python3.value,
            namePrefix="validator")
        self.prepared = True


class Python3Solution(AbstractExternalSolution, AbstractPython3):
    """
    Python3 implementation of external solution module.

    - argv: `[python3, modulepath, *super().argv]`
    """

    def __init__(self, *args, ioHelperModulePath: Path = None, **kwargs):
        self.ioHelperModulePath = ioHelperModulePath
        super().__init__(*args, **kwargs)

    @classmethod
    def generateArgs(
            cls, outfile: Path, modulePath: typing.Union[str, Path],
            *args, **kwargs) -> Const.ArgType:
        return ["python3",
                *super().generateArgs(outfile, modulePath, *args, **kwargs)]

    @classmethod
    def generateCode(
            cls, solutionPath: Path,
            parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType,
            ioHelperPath: Path, *args, **kwargs) -> str:
        return cls.replaceSymbols(
            cls.solutionTemplatePath,
            cls.templateDict(
                parameterInfo=parameterInfo,
                solutionPath=solutionPath, ioHelperPath=ioHelperPath,
                returnInfo=returnInfo, **kwargs)
        )

    def preparePipeline(self, *args, **kwargs):
        code = self.generateCode(
            self.originalModulePath, self.parameterInfo,
            self.returnInfo, self.ioHelperModulePath)
        self.modulePath = self.fs.newTempFile(
            code, extension=Const.SourceFileLanguage.Python3.value,
            namePrefix="solution")
        self.prepared = True
