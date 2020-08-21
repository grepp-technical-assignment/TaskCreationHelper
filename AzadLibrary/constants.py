"""
This module contains various constants for Azad library.
This module should not import any other part of Azad library.
"""

# Standard libraries
from enum import Enum
from decimal import Decimal
from fractions import Fraction
from sys import float_info
import typing


# Azad Library Version
AzadLibraryVersion = "0.3.0"


# Config defaults
SupportedConfigVersion = 1.0
DefaultFloatPrecision = 1e-3
DefaultIOPath = "IO"
DefaultInputSyntax = "%02d.in.txt"
DefaultOutputSyntax = "%02d.out.txt"
DefaultTimeLimit = 5.0  # seconds
DefaultMemoryLimit = 1024  # megabytes; Not used
MaxParameterDimensionAllowed = 2

# Log related
DefaultLoggingFilePath = "azadlib.log"
DefaultLogFileMaxSize = 10 * (2 ** 20)  # 10MB
DefaultLogFileBackups = 5  # blabla.log.%d
DefaultLogBaseFMT = "[%%(asctime)s][%%(levelname)-7s][%%(name)s][L%%(lineno)s] %%(message).%ds"
DefaultLogDateFMT = "%Y/%m/%d %H:%M:%S"

# Default typestring for all accepted types.
DefaultTypeStrings = {
    int: "int",
    float: "float",
    Decimal: "float",
    Fraction: "float",
    bool: "bool",
    str: "str"
}


def __IODataTypesInfo_StringConstraints(x: str):
    """
    Constraint function used for string I/O.
    """
    try:
        x.encode("ascii")
    except UnicodeEncodeError:
        return False
    else:
        return True


def __IODataTypesInfo_FloatStrize(x: typing.Union[float, Decimal, Fraction]):
    """
    Strize function for floating point numbers.
    """
    result = str(Decimal(x))
    if "." not in result:
        result += ".0"
    return result


# Information of I/O data types.
# If "constraint" is not in subdict,
#       then that type doesn't have any constraints.
IODataTypesInfo = {
    "int": {
        "pytypes": (int,),
        "constraint": (lambda x: -(2**31) <= x <= 2**31 - 1),
        "strize": (lambda x: "%d" % (x,)),
    },
    "long long": {
        "pytypes": (int,),
        "constraint": (lambda x: -(2**63) <= x <= 2**63 - 1),
        "strize": (lambda x: "%d" % (x,)),
    },
    "float": {
        "pytypes": (float, Decimal, Fraction, int),
        "constraint": (lambda x: 1.175494351e-38 <= abs(x) <= 3.402823466e38 or x == 0),
        "strize": __IODataTypesInfo_FloatStrize,
    },
    "double": {
        "pytypes": (float, Decimal, Fraction, int),
        "constraint": (lambda x: float_info.min <= abs(x) <= float_info.max or x == 0),
        "strize": __IODataTypesInfo_FloatStrize,
    },
    "str": {
        "pytypes": (str,),
        "constraint": __IODataTypesInfo_StringConstraints,
        "strize": (lambda x: "\"%s\"" % (x.replace('"', '\\"'),)),
    },
    "bool": {
        "pytypes": (bool, int),
        "constraint": (lambda x: isinstance(x, bool) or (x in (0, 1))),
        "strize": (lambda x: "true" if x else "false"),
    }
}
IODataTypesInfo["integer"] = IODataTypesInfo["int"]
IODataTypesInfo["long"] = IODataTypesInfo["long long"]
IODataTypesInfo["long long int"] = IODataTypesInfo["long long"]
IODataTypesInfo["real"] = IODataTypesInfo["double"]
IODataTypesInfo["string"] = IODataTypesInfo["str"]
IODataTypesInfo["boolean"] = IODataTypesInfo["bool"]

# Setup assertion
for typestr in IODataTypesInfo:
    dtinfo = IODataTypesInfo[typestr]
    if not isinstance(dtinfo, dict):
        raise TypeError(
            "IODataTypesInfo setup is wrong. Look %s." % (typestr,))
    elif not isinstance(dtinfo["pytypes"], (list, tuple)):
        raise TypeError(
            "IODataTypesInfo setup is wrong. Look %s, pytypes is wrong." % (typestr,))
    for t in dtinfo["pytypes"]:
        if not isinstance(t, type):
            raise TypeError(
                "IODataTypesInfo setup is wrong. Look %s, there is '%s' in pytypes." %
                (typestr, t))
    if not callable(dtinfo["constraint"]):
        raise ValueError(
            "IODataTypesInfo setup is wrong. Look %s, constraint is not callable." % (typestr,))
    elif not callable(dtinfo["strize"]):
        raise ValueError(
            "IODataTypesInfo setup is wrong. Look %s, strize is not callable." % (typestr,))


class SolutionCategory(Enum):
    """
    Enumeration of possible solution file status.
    """
    AC = "AC"
    WA = "WA"
    TLE = "TLE"
    MLE = "MLE"
    FAIL = "FAIL"


# Category of source file languages
class SourceFileLanguage(Enum):
    """
    Enumeration of possible solution file languages.
    """
    C = "c"
    Cpp = "cpp"
    Python3 = "py"
    Java = "java"
    Csharp = "cs"


# Default Config state
StartingConfigState = {
    "name": "none",
    "author": "unknown",
    "parameters": [
        {"name": "a", "type": "int", "dimension": 1},
        {"name": "b", "type": "str", "dimension": 0},
    ],
    "return": {"type": "float", "dimension": 2},
    "limits": {
        "time": DefaultTimeLimit,
        "memory": DefaultMemoryLimit
    },
    "solutions": {category.value: [] for category in SolutionCategory},
    "generators": {
        "sample": "put/your/path.py"
    },
    "genscript": [
        "sample big random 100 0.1",
        "sample small random 100 0.2"
    ],
    "log": "azadlib.log",  # Optional
    "iofiles": {
        "path": DefaultIOPath,
        "inputsyntax": DefaultInputSyntax,
        "outputsyntax": DefaultOutputSyntax,
    },
    "validator": "",
    "precision": DefaultFloatPrecision,
    "version": {
        "problem": 1.0,
        "config": SupportedConfigVersion
    }
}


# Log stuffs
class LogLevel(Enum):
    """
    Enumeration of logging level.
    """
    Error = "Error"
    Warn = "Warn"
    Info = "Info"
    Debug = "Debug"


# List of exit codes for multiprocessing
ExitCodeSuccess = 0
ExitCodeTLE = 33
ExitCodeMLE = 34
ExitCodeFailedToReturnData = 35
ExitCodeFailedInAVPhase = 36  # Failed in after-validation phase
ExitCodeFailedInBPPhase = 37  # Failed in before-preparation phase
ExitCodeFailedInLoopPhase = 38  # Failed in looping phase


# Target types for primitive data protocol
PrimitiveDataProtocolTargetTypes = typing.Union[
    int, float, bool, None,
    str, bytes, bytearray,
    list, tuple, set, frozenset,
    dict
]


# Sourcefile Types
class SourceFileType(Enum):
    """
    Enumeration of source file types.
    """
    Generator = "generator"
    Validator = "validator"
    Solution = "solution"
