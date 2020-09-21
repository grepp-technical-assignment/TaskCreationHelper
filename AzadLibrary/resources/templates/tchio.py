import typing
from sys import stdout, stderr
from decimal import Decimal
from fractions import Fraction
import traceback


def parseSingle(line: str, targetType: type) \
        -> typing.Union[int, float, bool]:
    """
    Parse the given line with given target type.
    """
    if targetType is int:
        return int(line)
    elif targetType is float:
        return float(line)
    elif targetType is bool:
        assert line in ("true", "false")
        return line == "true"
    else:
        raise TypeError("Unknown type t(%s)" % (targetType,))


def parseMulti(lines: typing.Iterator[str], targetType: type, dimension: int):
    """
    Parse multiple lines with given target type and dimension.
    """
    if dimension == 0:
        if targetType is not str:
            return parseSingle(next(lines), targetType)
        else:
            length = parseSingle(next(lines), int)
            return "".join(chr(parseSingle(next(lines), int))
                           for _ in range(length))
    else:
        size: int = parseSingle(next(lines), int)
        return [parseMulti(lines, targetType, dimension - 1)
                for _ in range(size)]


def printData(value: typing.Union[int, float, bool, str],
              targetType: type, dimension: int,
              file: typing.IO = stdout):
    """
    Output given value into output file.
    """
    if dimension > 0:
        assert isinstance(value, list)
        print(len(value), file=file)
        for element in value:
            printData(element, targetType, dimension - 1, file=file)
    elif targetType is int:
        assert isinstance(value, int)
        print(value, file=file)
    elif targetType is float:
        assert isinstance(value, (float, Decimal, Fraction))
        print("%.20g" % (value,), file=file)
    elif targetType is bool:
        assert isinstance(value, bool)
        print("true" if value else "false", file=file)
    elif targetType is str:
        assert isinstance(value, str)
        print(len(value), file=file)
        for ch in value:
            print(ord(ch), file=file)
    else:
        raise TypeError


def printException(err: Exception, file: typing.IO = stderr):
    """
    Report given exception(in standard Python style) to given file.
    """
    file.write("=" * 120 + "\n")
    traceback.print_exception(type(err), err, err.__traceback__, file=file)
