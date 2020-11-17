"""
This module contains exceptions for Azad library.
"""


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


class AzadTLE(AzadError, TimeoutError):
    """
    Raised when execution exceeded TLE.
    """


class AzadWarning(UserWarning):
    """
    Abstract class of all warnings.
    """


class TempFileSystemClosed(AzadWarning):
    """
    Warned when TempFileSystem is closed.
    """
