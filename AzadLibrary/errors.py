"""
This module contains exceptions for Azad library.
"""

# Azad library
from .constants import SolutionCategory


class AzadError(Exception):
    """
    Base abstraction of all Azad library errors.
    """


class FailedDataGeneration(AzadError):
    """
    Raised when data generation is failed.
    """


class FailedDataValidation(AzadError, ValueError, TypeError):
    """
    Raised when data validation is failed.
    """


class VersionError(AzadError):
    """
    Raised when version is different.
    """


class NotSupportedExtension(AzadError):
    """
    Raised when given file's extension is not supported.
    """

    def __init__(self, extension: str, additionalMessage: str = ""):
        super().__init__("Given extension %s is not supported. %s" %
                         (extension, additionalMessage))
        self.extension = extension


class WrongSolutionFileCategory(AzadError):
    """
    Raised when solution file's verdict is different from its category.
    """

    def __init__(self, sourceFileName, targetVerdict: SolutionCategory,
                 actualVerdict: SolutionCategory, additionalMessage: str = ""):
        super().__init__("Source file '%s' made verdict %s instead of %s. %s" %
                         (sourceFileName, actualVerdict, targetVerdict, additionalMessage))
        self.sourceFileName = sourceFileName
        self.targetVerdict = targetVerdict
        self.actualVerdict = actualVerdict


class AzadTLE(AzadError, TimeoutError):
    """
    Raised when execution exceeded TLE.
    """
