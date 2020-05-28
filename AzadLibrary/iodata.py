"""
This module is used to help I/O data (for problems) related.
"""

# Standard libraries
import typing
import os
from pathlib import Path
from decimal import Decimal
from fractions import Fraction

# Azad libraries
from .constants import (
    DefaultFloatPrecision,
    IODataTypesInfo, DefaultTypeStrings,
)


def cleanIOFilePath(path: typing.Union[str, Path],
                    targetExtensions: typing.Tuple[str] = ("in", "out", "txt")):
    """
    Remove all files with given extension in given path.
    """
    if isinstance(path, str):
        path = Path(path)
    for filename in path.iterdir():
        for extension in targetExtensions:
            if filename.name.endswith(extension):
                os.remove(filename)
                break


def YBMBizeData(data, typestr: str) -> str:
    """
    Transfer data into YBM-compatible string.
    """
    if isinstance(data, (list, tuple)):
        return "[%s]" % (",".join(YBMBizeData(d, typestr) for d in data),)
    else:
        return IODataTypesInfo[typestr]["strize"](data)


def checkPrecision(a: float, b: float,
                   precision: float = DefaultFloatPrecision):
    """
    Check similarity between two float numbers with given precision.
    """
    if precision <= 0:
        raise ValueError("Non-positive precision %f given" % (precision,))
    elif abs(a) <= 1e-10:
        return abs(a - b) <= precision
    else:
        return abs(a - b) <= precision or abs((a - b) / a) <= precision


def checkDataCompatibility(data, targetType: typing.Union[str, type]) -> bool:
    """
    Check data compatibilities.
    For integers, it should be in range of int32 or int64.
    For real numbers, it should be in range of IEEE float/double standard.
    For string, it should not contain any wide characters(wchar_t).
    """
    # Check each element's data range
    if isinstance(data, (list, tuple)):
        for element in data:
            if not checkDataCompatibility(element, targetType):
                return False
        return True

    # Clean datatype
    elif isinstance(targetType, type):  # Types should be converted to typestr
        targetType = DefaultTypeStrings[targetType]
    elif not isinstance(targetType, str):
        raise TypeError

    # Filtering unknown target type
    if targetType not in IODataTypesInfo:
        raise ValueError("Given target type '%s' is unknown" % (targetType,))

    # Given data is not matching to target type
    elif not isinstance(data, IODataTypesInfo[targetType]["pytypes"]):
        raise TypeError("Data type is %s but wanted to match %s(%s)" %
                        (type(data), targetType, IODataTypesInfo[targetType]["pytypes"]))

    # Check constraints
    else:
        return IODataTypesInfo[targetType]["constraint"](data)


def checkDataType(data, variableType: typing.Union[str, type, typing.Tuple[type]],
                  dimension: int, variableName: str = "??") -> bool:
    """
    Check data type and dimension. Return true if given data is valid.
    """
    if isinstance(variableType, str):  # Auto conversion
        variableType = IODataTypesInfo[variableType]["pytypes"]
    if dimension == 0:
        return isinstance(data, variableType)
    elif not isinstance(data, (list, tuple)):
        return False
    for element in data:
        if not checkDataType(element, variableType,
                             dimension - 1, variableName=variableName,):
            return False
    return True


def compareAnswers(*answers, floatPrecision: float = DefaultFloatPrecision):
    """
    Compare answers and return boolean value.
    Don't confuse, this function validates `(answer[1] == answer[2] == ... == answer[n])`.
    Consider first answer argument as main answer.
    """
    l = len(answers)
    if l < 2:
        raise ValueError("%d answer given to be compared. (Too small)" % (l,))

    # Dimension 1+
    if isinstance(answers[0], (list, tuple)):  # Iterable
        for i in range(l):
            if not isinstance(answers[i], (list, tuple)) or \
                    len(answers[0]) != len(answers[i]):
                return False
        for i in range(len(answers[0])):
            if not compareAnswers(*[answer[i] for answer in answers]):
                return False
        return True

    # Dimension 0
    else:
        for i in range(1, l):  # Type checking
            if not isinstance(answers[i], type(answers[0])):
                return False
        if isinstance(answers[0],
                      (float, Decimal, Fraction)):  # Float: Precision checking
            for i in range(1, l):
                if not checkPrecision(
                        answers[0], answers[i], floatPrecision):
                    return False
        elif isinstance(answers[0], (int, bool, str)):  # General cases
            for i in range(1, l):
                if answers[0] != answers[i]:
                    return False
        else:
            raise TypeError("Invalid answer type.")
        return True
