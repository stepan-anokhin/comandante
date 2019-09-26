"""Comandante domain model.

Description:
-----------

This module contains classes that describes notions
defined by the comandante toolkit: Commands, Options, etc.

This model classes are more or less declarations needed
for parsers and executors to interpret command line
arguments and execute the corresponding logic.
"""
import re


class Option:
    """Command option descriptor

    Each command option must have a valid name, type
    and could be required or not. If option is not
    required it may have a default value.
    """

    # Regex-pattern of valid option name.
    # Valid option name starts with alphabetic character and
    # its tail contain any number of alpha-numeric characters.
    _name_pattern = re.compile(r'\a\w+')

    @staticmethod
    def is_valid_name(name):
        """Check if the given name is a valid option name."""
        return isinstance(name, str) and bool(Option._name_pattern.fullmatch(name))

    def __init__(self, name, type=str, required=False, default=None):
        """Initialize an instance.

        Arguments:
        - name - must be a valid option name.
        - type - option value parser (unary function)
        - required - is the option required?
        - default - default option value

        """
        if not Option.is_valid_name(name):
            raise ValueError("'{name}' is not a valid option name".format(name=name))
        self._name = name
        self._type = type
        self._required = bool(required)
        self._default = default

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def required(self):
        return self._required

    @property
    def default(self):
        return self._default


class Command:
    """Command descriptor.

    The Command class represents command declaration.
    """
    # Regex-pattern of valid command name.
    # Valid command name starts with alphabetic character and
    # its tail contain any number of alpha-numeric characters.
    _name_pattern = re.compile(r'\a\w+')

    # Factory helpers:

    @staticmethod
    def is_valid_name(name):
        """Check if the given name is a valid command name."""
        return isinstance(name, str) and bool(Command._name_pattern.fullmatch(name))

    @staticmethod
    def extract_name(func):
        """Try to guess command name."""
        return func.__name__

    @staticmethod
    def extract_description(func):
        """Try to guess command description."""
        return func.__doc__ or ""

    @staticmethod
    def extract_usage(func):
        """Try to figure out command usage from target function."""
        # TODO: implement
        return ""

    @staticmethod
    def extract_brief(func):
        """Try to figure out command brief description from target function."""
        # TODO: implement
        return ""

    @staticmethod
    def from_callable(func):
        """Create and initialize a new Command descriptor from the given function."""
        return Command(
            name=Command.extract_name(func),
            usage=Command.extract_usage(func),
            brief=Command.extract_brief(func),
            description=Command.extract_description(func),
        )

    # Instance methods:

    def __init__(self, func, name, usage, brief, description=None):
        """Initialize an instance."""
        self._func = func
        self._name = name
        self._usage = usage
        self._brief = brief
        self._description = description
        self._options = {}

    def define_option(self, name, type=str, required=False, default=None):
        """Define a command option"""
        option = Option(name=name, type=type, required=required, default=default)
        self._options[option.name] = option

    # TODO: implement command properties
