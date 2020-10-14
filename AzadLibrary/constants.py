"""
This module contains various constants for Azad library.
This module should not import any other part of Azad library.
"""

# Standard libraries
from enum import Enum
from decimal import Decimal
from fractions import Fraction
import os
from sys import float_info
import typing
from pathlib import Path
import signal


# Azad Library Version
AzadLibraryVersion = "0.5.2"

# Extra constraints
MinimumPythonVersion = (3, 8, 3)

# Config defaults
SupportedConfigVersion = 1.0
DefaultFloatPrecision = 1e-6
DefaultIOPath = "IO"
DefaultInputSyntax = "%02d.in.txt"
DefaultOutputSyntax = "%02d.out.txt"
DefaultTimeLimit = 5.0  # seconds
DefaultMemoryLimit = 1024  # megabytes
MaxParameterDimensionAllowed = 2

# Generator, Validator related
DefaultGeneratorTL = 10.0
DefaultValidatorTL = 10.0

# Log related
DefaultLoggingFileName = "azadlib.log"
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

# Path to the resources folder
ResourcesPath = Path(os.path.abspath(__file__)).parent / "resources"


def __IODataTypesInfo_StringConstraints(x: str):
    """
    Constraint function used for string I/O.
    """
    try:
        x.encode("ascii")
    except UnicodeEncodeError:
        return False
    else:
        return '"' not in x


def __IODataTypesInfo_FloatStrize(x: typing.Union[float, Decimal, Fraction]):
    """
    Strize function for floating point numbers.
    """
    result = str(Decimal(x))
    if "." not in result:
        result += ".0"
    return result


def checkPrecision(a: float, b: float,
                   precision: float = DefaultFloatPrecision) -> bool:
    """
    Check similarity between two float numbers with given precision.
    """
    if precision <= 0:
        raise ValueError("Non-positive precision %f given" % (precision,))
    elif abs(a) <= precision ** 2:
        return abs(a - b) <= precision
    else:
        return abs(a - b) <= precision or abs((a - b) / a) <= precision


class IOVariableTypes(Enum):
    """
    Enumeration of I/O variable types in task.
    """
    INT = "int"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    STRING = "str"
    BOOL = "bool"


# Indirect names of IOVariableTypes.
IODataTypesIndirect = {
    IOVariableTypes.INT: {"integer", "int32"},
    IOVariableTypes.LONG: {"long long", "long long int", "int64"},
    IOVariableTypes.FLOAT: {"float32"},
    IOVariableTypes.DOUBLE: {"real", "float64"},
    IOVariableTypes.STRING: {"string", "char*"},
    IOVariableTypes.BOOL: {"boolean"}
}
for _iovt in IOVariableTypes:
    assert _iovt in IODataTypesIndirect


def getIOVariableType(s: str) -> IOVariableTypes:
    """
    Get IOVariableType of given string.
    """
    for iovt in IOVariableTypes:
        if s == iovt.value or s in IODataTypesIndirect[iovt]:
            return iovt
    raise ValueError("There is no such IODataType '%s'" % (s,))


# Information of I/O data types.
IODataTypesInfo = {
    IOVariableTypes.INT: {
        "pytypes": (int,),
        "constraint": (lambda x: -(2**31) <= x <= 2**31 - 1),
        "strize": (lambda x: "%d" % (x,)),
        "equal": (lambda x, y: x == y),
    },
    IOVariableTypes.LONG: {
        "pytypes": (int,),
        "constraint": (lambda x: -(2**63) <= x <= 2**63 - 1),
        "strize": (lambda x: "%d" % (x,)),
        "equal": (lambda x, y: x == y),
    },
    IOVariableTypes.FLOAT: {
        "pytypes": (float, Decimal, Fraction, int),
        "constraint": (lambda x: 1.175494351e-38 <= abs(x) <= 3.402823466e38 or x == 0),
        "strize": __IODataTypesInfo_FloatStrize,
        "equal": checkPrecision,
    },
    IOVariableTypes.DOUBLE: {
        "pytypes": (float, Decimal, Fraction, int),
        "constraint": (lambda x: float_info.min <= abs(x) <= float_info.max or x == 0),
        "strize": __IODataTypesInfo_FloatStrize,
        "equal": checkPrecision,
    },
    IOVariableTypes.STRING: {
        "pytypes": (str,),
        "constraint": __IODataTypesInfo_StringConstraints,
        "strize": (lambda x: "\"%s\"" % (x.replace('"', '\\"'),)),
        "equal": (lambda x, y: x == y),
    },
    IOVariableTypes.BOOL: {
        "pytypes": (bool, int),
        "constraint": (lambda x: isinstance(x, bool) or (x in (0, 1))),
        "strize": (lambda x: "true" if x else "false"),
        "equal": (lambda x, y: x == y),
    }
}
for _iovt in IODataTypesInfo:
    _dtinfo = IODataTypesInfo[_iovt]
    assert isinstance(_dtinfo, dict)
    assert set(_dtinfo.keys()) == {"pytypes", "constraint", "strize", "equal"}
    assert isinstance(_dtinfo["pytypes"], (list, tuple))
    for _t in _dtinfo["pytypes"]:
        assert isinstance(_t, type)
    assert callable(_dtinfo["constraint"])
    assert callable(_dtinfo["strize"])


class Verdict(Enum):
    """
    Enumeration of possible solution file status.
    """
    AC = "AC"
    WA = "WA"
    TLE = "TLE"
    MLE = "MLE"
    FAIL = "FAIL"


def getSolutionCategory(categoryStr: str) -> Verdict:
    """
    Get solution category corresponding to given string.
    """
    categoryStrUpper = categoryStr.upper()
    for category in Verdict:
        if category.value == categoryStrUpper:
            return category
    raise ValueError("Invalid category '%s'" % (categoryStr,))


class SourceFileLanguage(Enum):
    """
    Enumeration of possible solution file languages.
    """
    C = "c"
    Cpp = "cpp"
    Python3 = "py"
    Java = "java"
    Csharp = "cs"


def getSourceFileLanguage(extension: str) -> SourceFileLanguage:
    for lang in SourceFileLanguage:
        if lang.value == extension:
            return lang
    raise ValueError("Couldn't found language for '.%s'" % (extension,))


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
    "solutions": {category.value: [] for category in Verdict},
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


class ExitCode(Enum):
    """
    Enumeration of exit codes.
    """
    Success = 0  # Success
    GeneralUnintendedFail = 1  # Catchall for general errors
    InputParsingError = 3  # Failed to parse input
    MLE = -signal.SIGSEGV.value  # Memory Limit Exceeded / SIGSEGV
    WrongTypeGenerated = 5  # Result variable type is wrong
    ValidatorFailed = 6  # Validation function failed
    SolutionFailed = 7  # Solution function failed (Verdict FAIL)
    GeneratorFailed = 8  # Generator function failed
    TLE = -signal.SIGXCPU.value  # Time Limit Exceeded / SIGXCPU
    Killed = -signal.SIGKILL.value  # Killed by signal


class SourceFileType(Enum):
    """
    Enumeration of source file types.
    """
    Generator = "generator"
    Validator = "validator"
    Solution = "solution"


# Short name of type hints
OptionalPath = typing.Union[Path, None]
EXOO = typing.Tuple[ExitCode, OptionalPath,
                    OptionalPath]  # (ExitCode, outfile, stderr)
ArgType = typing.List[typing.Union[str, Path]]
ParamInfoSingle = typing.Tuple[str, IOVariableTypes, int]
ParamInfoList = typing.List[ParamInfoSingle]
ReturnInfoType = typing.Tuple[IOVariableTypes, int]


class AzadLibraryMode(Enum):
    """
    Enumeration of Azad library mode.
    """
    Full = "full"  # Full produce and validation
    Produce = "produce"  # Produce AC data only
    GenerateCode = "generate_code"  # Generate code for external module only
    Help = "help"  # Print help only
