"""
This module prepares function to be executed.
"""

# Standard libraries
import typing
from pathlib import Path
import importlib
import hashlib

# Azad libraries
from .constants import SourceFileLanguage, SourceFileType


def getExtension(filePath: typing.Union[str, Path]) -> str:
    """
    Get extension of given file.
    """
    if isinstance(filePath, str):
        return filePath.split(".")[-1]
    elif isinstance(filePath, Path):
        if filePath.is_file():
            return filePath.name.split(".")[-1]
        else:
            raise FileNotFoundError
    else:
        raise TypeError


def getSourceFileLanguage(
        sourceFilePath: typing.Union[str, Path]) -> typing.Union[SourceFileLanguage, None]:
    """
    Get language of given source file.
    If there is no matching language then give None.
    """
    extension: str = getExtension(sourceFilePath)
    for lang in SourceFileLanguage:
        if lang.value == extension:
            return lang
    else:
        return None


def prepareModule_old(sourceFilePath: typing.Union[str, Path],
                      moduleName: str):
    """
    Prepare module from given file name.
    This function is scheduled to be removed.
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


def prepareExecFunc(sourceFilePath: typing.Union[str, Path],
                    sourceFileType: SourceFileType) \
        -> importlib.types.FunctionType:
    """
    Prepare function to execute from given file name and sourcefile type.
    Note that this function will be decorated again in AzadProcess.
    See process submodule for further details.
    """
    # Get filename extension
    fileExtension = getExtension(sourceFilePath)
    sourceLanguage = getSourceFileLanguage(sourceFilePath)

    # Python
    if sourceLanguage is SourceFileLanguage.Python3:

        # Common: Prepare module
        spec = importlib.util.spec_from_file_location(
            sourceFileType.name, sourceFilePath)
        thisModule = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(thisModule)

        # Return different functions by sourcefile type
        if sourceFileType is SourceFileType.Generator:
            return thisModule.generate
        elif sourceFileType is SourceFileType.Solution:
            return thisModule.solution
        elif sourceFileType is SourceFileType.Validator:
            return thisModule.validate
        else:
            raise NotImplementedError

    # Other languages are unsupported
    elif isinstance(sourceLanguage, SourceFileLanguage):
        raise NotImplementedError
    else:
        raise TypeError("Invalid sourcefile type %s given" %
                        (type(sourceLanguage),))
