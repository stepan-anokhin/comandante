"""Comandante exception hierarchy.

Description:
-----------

This module contains classes representing errors related to
command line interface logic.
"""


class CliException(Exception):
    """Parent class for all comandante-related exceptions."""
    pass


class CliSyntaxException(CliException):
    """Indicates wrong command line syntax."""
    pass


class ArgumentMissing(CliSyntaxException):
    """Raised when a required argument is missing."""


class TooManyArguments(CliSyntaxException):
    """Raised when there are too many cli-arguments."""


class InvalidValue(CliSyntaxException):
    """Raised when argument or option value has invalid syntax."""


class MissingOptionValue(CliSyntaxException):
    """Raised when option value is missing."""


class UnknownOption(CliSyntaxException):
    """Raised when unknown option is provided."""


class DuplicateOption(CliSyntaxException):
    """Raised when some option is specified twice."""


class UnknownCommand(CliSyntaxException):
    """Raised when unknown command is invoked."""
