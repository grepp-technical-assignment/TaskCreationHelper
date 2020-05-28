"""
This module helps to check syntax of many things.
"""

# Standard libraries
import re
import typing

# Variable name syntax
variableNamePattern = "[a-z_][a-zA-Z0-9_]{0,15}"
bannedVariableNames = (
    "int", "str", "bool", "long", "float", "double", "short",  # Direct type names
    "integer", "string", "boolean", "number",
    "vector", "set", "queue", "list", "dict", "map", "array",  # Data structures
    "size", "len", "length", "filter",  # Built-in functions
    "for", "if", "else", "while", "def",  # Keywords
    "try", "catch", "except", "finally", "fn",  # Keywords
    "solution", "answer",
)
variableNamePattern = re.compile("(?!(%s)$)(%s)" % (
    "|".join("%s" % (name,) for name in bannedVariableNames), variableNamePattern))

# IO file syntax's syntax
freeIONamePattern = "[a-zA-Z0-9_\\-]+"
enumeratePattern = "%0?([2-9]|([1-9][0-9]+))d"
inputFileSuffixPattern = "\\.in(\\.txt)?"
outputFileSuffixPattern = "\\.out(\\.txt)?"
inputFilePattern = re.compile("(%s)?%s(%s)?%s" % (
    freeIONamePattern, enumeratePattern,
    freeIONamePattern, inputFileSuffixPattern))
outputFilePattern = re.compile("(%s)?%s(%s)?%s" % (
    freeIONamePattern, enumeratePattern,
    freeIONamePattern, outputFileSuffixPattern))

# genscript syntax
generatorNamePattern = re.compile("[a-zA-Z0-9_]+")
genscriptLinePattern = re.compile(
    "%s( \\S+)*" % (generatorNamePattern.pattern,))
genscriptCommentPattern = re.compile("()|((#|(//)).*)")


def cleanGenscript(
        genscript: typing.List[str], generatorNames: typing.Iterable) -> typing.List[str]:
    """
    Validate given genscript with generator names.
    If a syntax error found, raise SyntaxError.
    """
    generatorNames = list(generatorNames)
    result = []
    i = 0
    for line in genscript:
        i += 1
        if not isinstance(line, str):
            raise TypeError(
                "Invalid type %s given for genscript line" % (type(line),))
        elif genscriptCommentPattern.fullmatch(line):
            continue  # Comment should pass
        elif not genscriptLinePattern.fullmatch(line):
            raise SyntaxError(
                "Genscript line %d '%s' doesn't match syntax" % (i, line))
        generatorName = line.split(" ")[0]
        if generatorName not in generatorNames:
            raise SyntaxError("Genscript line %d '%s' targetted non-existing generator %s" %
                              (i, line, generatorName))
        result.append(line)
    return result


if __name__ == "__main__":  # Interactive testing

    def interactive_test(pattern: str, name: str):
        line = input("Enter for %s: " % (name,))
        if line.upper() == "EXIT":
            exit()
        return bool(re.fullmatch(pattern, line))

    targetTestObject = "genscript comment"
    while True:
        testresult = interactive_test(
            genscriptCommentPattern, targetTestObject)
        if testresult:
            print("Good %s." % (targetTestObject,))
        else:
            print("Bad %s." % (targetTestObject,))
