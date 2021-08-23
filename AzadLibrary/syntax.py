"""
This module helps to check syntax of many things.
"""

# Standard libraries
import re
import typing

# Variable name syntax
variableNamePattern = "[a-z_][a-z0-9_]{0,15}"  # Lowercase only
bannedVariableNames = {

    # C++ keywords: https://en.cppreference.com/w/cpp/keyword
    "alignas", "alignof", "and", "and_eq", "asm",
    "atomic_cancel", "atomic_commit", "atomic_noexcept",
    "auto", "bitand", "bitor", "bool", "break",
    "case", "catch", "char", "char8_t", "char16_t", "char32_t",
    "class", "compl", "concept", "const", "consteval",
    "constexpr", "constinit", "const_cast", "continue",
    "co_await", "co_return", "co_yield", "decltype", "default",
    "delete", "do", "double", "dynamic_cast", "else", "enum",
    "explicit", "export", "extern", "false", "float", "for",
    "friend", "goto", "if", "inline", "int", "long", "mutable",
    "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
    "operator", "or", "or_eq", "private", "protected", "public",
    "reflexpr", "register", "reinterpret_cast", "requires",
    "return", "short", "signed", "sizeof", "static",
    "static_assert", "static_cast", "struct", "switch",
    "synchronized", "template", "this", "thread_local", "throw",
    "true", "try", "typedef", "typeid", "typename", "union",
    "unsigned", "using", "virtual", "void", "volatile", "wchar_t",
    "while", "xor", "xor_eq",

    # C++ containers: https://en.cppreference.com/w/cpp/container
    "array", "vector", "deque", "forward_list", "list", "set",
    "map", "multiset", "multimap", "unordered_set", "unordered_map",
    "unordered_multiset", "unordered_multimap", "stack", "queue",
    "priority_queue", "span",

    # C++ extra containers
    "pair", "tuple", "bitset",

    # Java keywords:
    # https://docs.oracle.com/javase/tutorial/java/nutsandbolts/_keywords.html
    "abstract", "assert", "boolean", "break", "byte", "case",
    "catch", "char", "class", "const", "continue", "default",
    "do", "double", "else", "enum", "extends", "final", "finally",
    "float", "for", "goto", "if", "implements", "import",
    "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return",
    "short", "static", "strictfp", "super", "switch",
    "synchronized", "this", "throw", "throws", "transient",
    "try", "void", "volatile", "while",

    # Python keywords:
    # https://docs.python.org/3/reference/lexical_analysis.html#keywords
    "and", "as", "assert", "async",
    "await", "break", "class", "continue", "def", "del", "elif",
    "else", "except", "finally", "for", "from", "global", "if",
    "import", "in", "is", "lambda", "nonlocal", "not", "or",
    "pass", "raise", "return", "try", "while", "with", "yield",

    # Python builtins:
    # https://docs.python.org/3/library/functions.html#built-in-functions
    # https://docs.python.org/3/library/constants.html
    "abs", "all", "any", "ascii", "bin", "bool", "breakpoint",
    "bytearray", "bytes", "callable", "chr", "classmethod", "compile",
    "complex", "delattr", "dict", "dir", "divmod", "enumerate",
    "eval", "exec", "filter", "float", "format", "frozenset",
    "getattr", "globals", "hasattr", "hash", "help", "hex", "id",
    "input", "int", "isinstance", "issubclass", "iter", "len", "list",
    "locals", "map", "max", "memoryview", "min", "next", "object",
    "oct", "open", "ord", "pow", "print", "property", "range", "repr",
    "reversed", "round", "set", "setattr", "slice", "sorted",
    "staticmethod", "str", "sum", "super", "tuple", "type", "vars",
    "zip", "__import__", "__debug__",

    # JS keywords:
    # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Lexical_grammar#reserved_keywords_as_of_ecmascript_2015
    "break", "case", "catch", "class", "const", "continue",
    "debugger", "default", "delete", "do", "else", "export",
    "extends", "finally", "for", "function", "if", "import",
    "in", "instanceof", "new", "return", "super", "switch",
    "this", "throw", "try", "typeof", "var", "void",
    "while", "with", "yield",

    # JS keywords - Future reserved
    "enum", "implements", "interface", "let", "package",
    "private", "protected", "public", "static", "yield", "await",

    # C# keywords:
    # https://docs.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/
    "abstract", "as", "base", "bool", "break", "byte", "case",
    "catch", "char", "checked", "class", "const", "continue",
    "decimal", "default", "delegate", "do", "double", "else",
    "enum", "event", "explicit", "extern", "false", "finally",
    "fixed", "float", "for", "foreach", "goto", "if", "implicit",
    "in", "int", "interface", "internal", "is", "lock", "long",
    "namespace", "new", "null", "object", "operator", "out",
    "override", "params", "private", "protected", "public",
    "readonly", "ref", "return", "sbyte", "sealed", "short",
    "sizeof", "stackalloc", "static", "string", "struct",
    "switch", "this", "throw", "true", "try", "typeof", "uint",
    "ulong", "unchecked", "unsafe", "ushort", "using", "virtual",
    "void", "volatile", "while",

    # Kotlin keywords: https://kotlinlang.org/docs/keyword-reference.html
    # Wrote hard keywords only
    "as", "break", "class", "continue", "do", "else", "false",
    "for", "if", "in", "interface", "is", "null", "object",
    "package", "return", "super", "this", "throw", "true",
    "try", "typealias", "typeof", "val", "var", "when", "while",

    # Extra
    "solution", "answer",
}
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
