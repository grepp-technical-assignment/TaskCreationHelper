import typing
from sys import stderr
from decimal import Decimal
from fractions import Fraction
import traceback


def yieldInputLines(file: typing.IO[str]):
    """
    Yield each line from input.
    """
    yield from file.read().split("\n")


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


def yieldStrized(value: typing.Union[int, float, bool, str],
                 targetType: type, dimension: int) -> typing.Iterator[str]:
    """
    Yield each part of strized data from
    given value and target type/dimension.
    """
    if dimension > 0:
        assert isinstance(value, (list, tuple))
        yield str(len(value))
        for element in value:
            yield from yieldStrized(element, targetType, dimension - 1)
    elif targetType is int:
        assert isinstance(value, int)
        yield str(value)
    elif targetType is float:
        assert isinstance(value, (float, Decimal, Fraction))
        yield "%.20g" % (value,)
    elif targetType is bool:
        assert isinstance(value, bool)
        yield "true" if value else "false"
    elif targetType is str:
        assert isinstance(value, str)
        yield str(len(value))
        yield from (str(ord(ch)) for ch in value)
    else:
        raise TypeError


def printData(value: typing.Union[int, float, bool, str],
              targetType: type, dimension: int,
              file: typing.IO):
    """
    Output given value into output file.
    Assume given file is opened in binary mode.
    """
    file.write(b'\n'.join(
        c.encode('ascii') for c in
        yieldStrized(value, targetType, dimension)))
    file.write(b'\n')


def printException(err: Exception, file: typing.IO = stderr):
    """
    Report given exception(in standard Python style) to given file.
    """
    file.write("=" * 120 + "\n")
    traceback.print_exception(type(err), err, err.__traceback__, file=file)
