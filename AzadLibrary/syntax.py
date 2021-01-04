"""
This module helps to check syntax of many things.
"""

# Standard libraries
import re
import typing

# Variable name syntax
variableNamePattern = "[a-z_][a-z0-9_]{0,15}"  # Lowercase only
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

# File extension syntax
extensionSyntax = re.compile("[a-zA-Z][a-zA-Z0-9]*")


def cleanGenscript(genscript: str, generatorNames: typing.Iterable) -> \
        typing.Union[typing.List[str], None]:
    """
    Validate given genscript with existing generator names.
    Assume that given generator names are already verified.
    - If given genscript is comment, return None.
    - Else if any syntax error found, raise SyntaxError.
    - Otherwise, return splitted version of genscript.
    """
    genscript = genscript.strip()
    if genscriptCommentPattern.fullmatch(genscript):  # Comment
        return None
    elif not genscriptLinePattern.fullmatch(genscript):
        raise SyntaxError(
            "Genscript '%s' does not satisfy syntax" % (genscript,))
    generatorName = genscript.split(" ")[0]
    if generatorName not in generatorNames:
        raise SyntaxError("Unknown generator name '%s' in genscript" %
                          (generatorName,))
    else:
        return [x for x in genscript.split(" ") if x]


if __name__ == "__main__":  # Interactive testing

    pass
