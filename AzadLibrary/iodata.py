"""
This module is used to define and support I/O data (for problems) related stuffs.
"""

# Standard libraries
import typing
import os
from pathlib import Path

# Azad libraries
from . import constants as Const


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


def yieldLines(file: typing.IO[str]) -> typing.Iterator[str]:
    """
    Read and yield each line until to reach end of file.
    """
    while True:
        line: str = file.readline()
        if line == '':
            break
        yield line.replace("\n", "")


def PGizeData(data, iovt: Const.IOVariableTypes) -> str:
    """
    Transfer data into Programmers-compatible string.
    """
    if isinstance(data, (list, tuple)):
        return "[%s]" % (",".join(PGizeData(d, iovt) for d in data),)
    else:
        return Const.IODataTypesInfo[iovt]["strize"](data)


def parseSingle(line: str, targetType: Const.IOVariableTypes) \
        -> typing.Union[int, float, bool]:
    """
    Parse the given line with given target type.
    """
    if targetType in (Const.IOVariableTypes.INT, Const.IOVariableTypes.LONG):
        return int(line)
    elif targetType in (Const.IOVariableTypes.FLOAT, Const.IOVariableTypes.DOUBLE):
        return float(line)
    elif targetType is Const.IOVariableTypes.BOOL:
        if line not in ("true", "false"):
            raise ValueError
        return line == "true"
    else:
        raise TypeError("Unknown type t(%s) for single parse" % (targetType,))


def parseMulti(lines: typing.Iterator[str],
               targetType: Const.IOVariableTypes, dimension: int):
    """
    Parse multiple lines with given target type and dimension.
    This may raise ValueError.
    """
    if dimension == 0:
        if targetType is not Const.IOVariableTypes.STRING:
            result = parseSingle(next(lines), targetType)
        else:
            length = parseSingle(next(lines), Const.IOVariableTypes.INT)
            result = "".join(chr(parseSingle(next(lines), Const.IOVariableTypes.INT))
                             for _ in range(length))
        if not Const.IODataTypesInfo[targetType]["constraint"](result):
            raise ValueError("Parsed data failed on constraint func")
        return result
    else:
        size: int = parseSingle(next(lines), int)
        result = [parseMulti(lines, targetType, dimension - 1)
                  for _ in range(size)]
        if dimension > 1 and len(set(len(element) for element in result)) > 1:
            raise ValueError("Generated non-rectangle array")
        return result


def isCorrectAnswer(answer, produced, returnType: Const.IOVariableTypes,
                    dimension: int) -> bool:
    """
    Return if produced answer is correct.
    """
    if dimension > 0:
        if not isinstance(produced, list) or len(answer) != len(produced):
            return False
        for element1, element2 in zip(answer, produced):
            if not isCorrectAnswer(
                    element1, element2, returnType, dimension - 1):
                return False
        return True
    else:
        return Const.IODataTypesInfo[returnType]["equal"](answer, produced)
