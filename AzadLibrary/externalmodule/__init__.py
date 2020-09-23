"""
This module provides top interface of external module features.
"""

# Standard libraries

# Azad libraries
from .. import constants as Const
from ..errors import AzadError
from .abstract import (
    AbstractExternalModule, AbstractProgrammingLanguage,
    AbstractExternalGenerator, AbstractExternalValidator,
    AbstractExternalSolution
)
from .python3 import (
    AbstractPython3, Python3Generator, Python3Validator, Python3Solution
)
from .cpp import (
    AbstractCpp, CppGenerator, CppSolution, CppValidator
)

_classes = {
    Const.SourceFileLanguage.Python3: {
        Const.SourceFileType.Generator: Python3Generator,
        Const.SourceFileType.Validator: Python3Validator,
        Const.SourceFileType.Solution: Python3Solution
    },
    Const.SourceFileLanguage.Cpp: {
        Const.SourceFileType.Generator: CppGenerator,
        Const.SourceFileType.Validator: CppValidator,
        Const.SourceFileType.Solution: CppSolution,
    }
}


def getExternalModuleClass(
        lang: Const.SourceFileLanguage,
        sourceType: Const.SourceFileType) -> type:
    try:
        return _classes[lang][sourceType]
    except (KeyError, IndexError) as err:
        raise AzadError(
            "Unsupported Lang %s / Type %s" %
            (lang.name, sourceType.name)).with_traceback(err.__traceback__)
