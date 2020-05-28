# Standard libraries
import typing
from pathlib import Path

# Azad library
from .constants import SourceFileLanguage


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
    return None
