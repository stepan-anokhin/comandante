"""Comandante exception hierarchy.

Description:
-----------

This module contains classes representing errors related to
command line interface logic.
"""
from comandante.inner.helpers import getname


class CliException(Exception):
    """Parent class for all comandante-related exceptions."""
    pass


class CliSyntaxException(CliException):
    """Indicates wrong command line syntax."""


class ArgumentMissing(CliSyntaxException):
    """Raised when a required argument is missing."""

    def __init__(self, argument):
        self.argument = argument
        super(ArgumentMissing, self).__init__("Required argument is not specified: '{name}'".format(name=argument.name))


class TooManyArguments(CliSyntaxException):
    """Raised when there are too many cli-arguments."""

    def __init__(self, message=None):
        super(TooManyArguments, self).__init__(message or "Too many arguments")


class InvalidArgumentValue(CliSyntaxException):
    """Raised when argument or option value has invalid syntax."""

    def __init__(self, argument, value):
        pattern = "Invalid value for argument '{name}' of type '{type}': '{value}'"
        error_message = pattern.format(name=argument.name, type=getname(argument.type), value=value)
        super(InvalidArgumentValue, self).__init__(error_message)
        self.argument = argument
        self.value = value


class InvalidOptionValue(CliSyntaxException):
    """Raised when argument or option value has invalid syntax."""

    def __init__(self, option, value):
        pattern = "Invalid value for option '{name}' of type '{type}': '{value}'"
        error_message = pattern.format(name=option.name, type=getname(option.type), value=value)
        super(InvalidOptionValue, self).__init__(error_message)
        self.option = option
        self.value = value


class MissingOptionValue(CliSyntaxException):
    """Raised when option value is missing."""

    def __init__(self, option):
        super(MissingOptionValue, self).__init__("Option '{name}' is missing its value".format(name=option.name))
        self.option = option


class UnknownOption(CliSyntaxException):
    """Raised when unknown option is provided."""

    def __init__(self, name):
        super(UnknownOption, self).__init__("Unknown option: '{name}'".format(name=name))
        self.name = name


class DuplicateOption(CliSyntaxException):
    """Raised when some option is specified twice."""

    def __init__(self, name):
        super(DuplicateOption, self).__init__("Duplicated option: '{name}'".format(name=name))
        self.name = name


class UnknownCommand(CliSyntaxException):
    """Raised when unknown command is invoked."""

    def __init__(self, command):
        super(UnknownCommand, self).__init__("Unknown command: '{name}'".format(name=command))
        self.command = command
