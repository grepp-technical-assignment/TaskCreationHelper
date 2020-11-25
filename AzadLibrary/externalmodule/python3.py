"""
This module provides implementation of Python3 external module.
"""

# Standard libraries
import typing
from pathlib import Path

# Azad libraries
from .. import constants as Const
from ..misc import isExistingFile, removeExtension
from ..errors import AzadError
from .abstract import (
    AbstractProgrammingLanguage, AbstractExternalGenerator,
    AbstractExternalValidator, AbstractExternalSolution)


class AbstractPython3(AbstractProgrammingLanguage):
    """
    Python3 specification of abstract programming language.
    """

    baseTypeStrTable = {
        Const.IOVariableTypes.INT: "int",
        Const.IOVariableTypes.LONG: "int",
        Const.IOVariableTypes.FLOAT: "float",
        Const.IOVariableTypes.DOUBLE: "float",
        Const.IOVariableTypes.BOOL: "bool",
        Const.IOVariableTypes.STRING: "str"
    }

    @classmethod
    def typeStr(cls, iovt: Const.IOVariableTypes, dimension: int):
        return cls.baseTypeStrTable[iovt] if dimension == 0 else \
            "typing.List[%s]" % cls.typeStr(iovt, dimension - 1)

    # Template file path
    generatorTemplatePath = Const.ResourcesPath / \
        "templates/generator_python3.template"
    solutionTemplatePath = Const.ResourcesPath / \
        "templates/solution_python3.template"
    validatorTemplatePath = Const.ResourcesPath / \
        "templates/validator_python3.template"
    ioHelperTemplatePath = Const.ResourcesPath / "helpers/tchio.py"

    # Indent level
    indentLevelGetParameter = 2
    indentLevelPutParameter = 2

    @classmethod
    def templateDict(
            cls, *args,
            parameterInfo: typing.List[typing.Tuple[
                str, Const.IOVariableTypes, int]] = (),
            generatorPath: Path = None, validatorPath: Path = None,
            solutionPath: Path = None, ioHelperPath: Path = None,
            returnInfo: Const.ReturnInfoType = None,
            **kwargs) -> dict:

        # Language-common state
        result = super().templateDict(**kwargs)

        # Get all parameters (for validator and solutions)
        result["GetParameters"] = cls.leveledNewline(cls.indentLevelGetParameter).join(
            cls.generateCodeGetParameter(*param) for param in parameterInfo)

        # Print all parameters (for generators)
        result["PrintParameters"] = cls.leveledNewline(cls.indentLevelPutParameter).join(
            cls.generateCodePutParameter(*param) for param in parameterInfo)

        # Result info
        if returnInfo:
            returnType, returnDimension = returnInfo
            result["ReturnTypeBase"] = cls.typeStr(returnType, 0)
            result["ReturnDimension"] = returnDimension

        def registerPath(key: str, path: Path):
            if path:
                if not isExistingFile(path):
                    raise OSError(
                        "Given path(key = %s, path = %s) isn't existing file" %
                        (key, path))
                result[key] = removeExtension(path)

        # Set paths
        registerPath("GeneratorPath", generatorPath)
        registerPath("ValidatorPath", validatorPath)
        registerPath("SolutionPath", solutionPath)
        registerPath("PythonIOHelperPath", ioHelperPath)

        # Return
        return result

    @classmethod
    def generateCodeGetParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        tReal = cls.typeStr(parameterType, 0)
        tHint = cls.typeStr(parameterType, parameterDimension)
        return "inputValues['%s']: %s = TCHIO.parseMulti(inputLineIterator, %s, %d)" % \
            (variableName, tHint, tReal, parameterDimension)

    @classmethod
    def generateCodePutParameter(
            cls, variableName: str,
            parameterType: Const.IOVariableTypes,
            parameterDimension: int) -> str:
        tReal = cls.typeStr(parameterType, 0)
        return "TCHIO.printData(generated['%s'], %s, %s, file = outfile); del generated['%s']" % \
            (variableName, tReal, parameterDimension, variableName)


class Python3Generator(AbstractExternalGenerator, AbstractPython3):
    """
    Python3 implementation of external generator module.
    `generateCompilationArgs` is not implemented,
    because Python3 does not need compilation process.

    - argv: `[python3, modulepath, *super().argv]`
    """

    # Indent level
    indentLevelGetParameter = 3
    indentLevelPutParameter = 3

    def __init__(self, *args, ioHelperModulePath: Path = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ioHelperModulePath = self.newTempFileByCopy(
            ioHelperModulePath, extension="py", namePrefix="iohelper")

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

    @classmethod
    def generateExecutionArgs(
            cls, outfile: typing.Union[str, Path],
            genscript: typing.List[str],
            modulePath: typing.Union[str, Path],
            *args, **kwargs) -> Const.ArgType:
        return ["python3", *super().generateExecutionArgs(
            outfile, genscript, modulePath, *args, **kwargs)]

    def preparePipeline(self):
        if self.prepared:
            raise AzadError("Already prepared")
        code = self.generateCode(
            self.originalSourceCodePath, self.parameterInfo,
            self.ioHelperModulePath)
        self.modulePath = self.newTempFile(
            extension=Const.SourceFileLanguage.Python3.value,
            namePrefix="generator", content=code)
        self.prepared = True


class Python3Validator(AbstractExternalValidator, AbstractPython3):
    """
    Python3 implementation of external validator module.
    `generateCompilationArgs` is not implemented,
    because Python3 does not need compilation process.

    - argv: `[python3, modulepath, *super().argv]`
    """

    def __init__(self, *args, ioHelperModulePath: Path = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ioHelperModulePath = self.newTempFileByCopy(
            ioHelperModulePath, extension="py", namePrefix="iohelper")

    @classmethod
    def generateCode(
            cls, validatorPath: Path, parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType, ioHelperPath: Path,
            *args, **kwargs) -> str:
        return cls.replaceSymbols(
            cls.validatorTemplatePath, cls.templateDict(
                parameterInfo=parameterInfo,
                validatorPath=validatorPath, ioHelperPath=ioHelperPath,
                **kwargs)
        )

    @classmethod
    def generateExecutionArgs(
            cls, modulePath: typing.Union[str, Path],
            *args, **kwargs) -> Const.ArgType:
        return ["python3",
                *super().generateExecutionArgs(modulePath, *args, **kwargs)]

    def preparePipeline(self):
        if self.prepared:
            raise AzadError("Already prepared")
        code = self.generateCode(
            self.originalSourceCodePath, self.parameterInfo,
            self.returnInfo, self.ioHelperModulePath)
        self.modulePath = self.newTempFile(
            extension=Const.SourceFileLanguage.Python3.value,
            namePrefix="validator", content=code)
        self.prepared = True


class Python3Solution(AbstractExternalSolution, AbstractPython3):
    """
    Python3 implementation of external solution module.
    `generateCompilationArgs` is not implemented,
    because Python3 does not need compilation process.

    - argv: `[python3, modulepath, *super().argv]`
    """

    def __init__(self, *args, ioHelperModulePath: Path = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ioHelperModulePath = self.newTempFileByCopy(
            ioHelperModulePath, extension="py", namePrefix="iohelper")

    @classmethod
    def generateCode(
            cls, solutionPath: Path,
            parameterInfo: Const.ParamInfoList,
            returnInfo: Const.ReturnInfoType,
            ioHelperPath: Path, *args, **kwargs) -> str:
        return cls.replaceSymbols(
            cls.solutionTemplatePath, cls.templateDict(
                parameterInfo=parameterInfo,
                solutionPath=solutionPath, ioHelperPath=ioHelperPath,
                returnInfo=returnInfo, **kwargs)
        )

    @classmethod
    def generateExecutionArgs(
            cls, outfile: Path, modulePath: typing.Union[str, Path],
            *args, **kwargs) -> Const.ArgType:
        return ["python3", *super().generateExecutionArgs(
            outfile, modulePath, *args, **kwargs)]

    def preparePipeline(self):
        if self.prepared:
            raise AzadError("Already prepared")
        code = self.generateCode(
            self.originalSourceCodePath, self.parameterInfo,
            self.returnInfo, self.ioHelperModulePath)
        self.modulePath = self.newTempFile(
            extension=Const.SourceFileLanguage.Python3.value,
            namePrefix="solution", content=code)
        self.prepared = True
