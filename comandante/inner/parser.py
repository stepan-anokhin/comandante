"""Command line argument parsing.

Description:
-----------

This module defines a `Parser` class which is responsible
for reading and interpreting command-line arguments according
to the command line description in terms of domain model.
"""

import sys
from collections import deque

import comandante.errors as error

if sys.version_info > (3, 0):
    from itertools import zip_longest
else:
    from itertools import izip_longest as zip_longest


class Parser:
    """Command-line arguments parser.

    The sole responsibility of the `Parser` is to take a command
    domain model in terms of options and arguments and then
    interpret command-line arguments accordingly.
    """

    def __init__(self, signature, declared_options):
        """Initialize instance.

        :param signature: command signature
        :param declared_options: declared options
        """
        self._signature = signature
        self._long_options, self._short_options = {}, {}
        for option in declared_options:
            self._long_options[option.name] = option
            self._short_options[option.short] = option

    @staticmethod
    def more_options(cli_arguments):
        """Check if the cli argument sequence begins with option."""
        return len(cli_arguments) > 0 and cli_arguments[0].startswith('-')

    def parse(self, cli_arguments):
        """Parse command line arguments.

        :param cli_arguments: raw command line arguments sequence

        :return: (options, arguments) tuple
        """
        cli_arguments = self._make_deque(cli_arguments)
        options = self._parse_options(cli_arguments)
        arguments = self._parse_arguments(cli_arguments)
        return options, arguments

    @staticmethod
    def _make_deque(cli_arguments):
        if not isinstance(cli_arguments, deque):
            return deque(cli_arguments)
        return cli_arguments

    @staticmethod
    def _parse_long_option(equation):
        if '=' not in equation:
            return equation[2:], None
        return equation[2:].split('=', 1)

    def _parse_options(self, cli_arguments):
        """Parse options.

        :param cli_arguments: a list containing raw command-line arguments
        :return: a dict containing option values and remaining command-line arguments
        """
        options = {}
        while self.more_options(cli_arguments):
            name, value = self._parse_option(cli_arguments)
            if name in options:
                raise error.DuplicateOption(name)
            options[name] = value

        return options

    def _parse_option(self, cli_arguments):
        """Parse a single option from the remaining raw command-line arguments"""
        option = self._get_option(cli_arguments)
        parser = self._get_option_parser(option)
        value = parser(cli_arguments)
        return option.name, value

    def _get_option(self, cli_arguments):
        """Get option given the remaining cli-arguments."""
        if not cli_arguments:
            raise RuntimeError('Empty CLI arguments')
        if not self.more_options(cli_arguments):
            raise RuntimeError("CLI arguments doesn't contain options")

        first = cli_arguments.popleft()
        if first.startswith('--'):
            name, value = self._parse_long_option(first)
            if name not in self._long_options:
                raise error.UnknownOption(first)
            if value is not None:
                cli_arguments.appendleft(value)
            return self._long_options[name]
        elif first.startswith('-'):
            name = first[1:]
            if name not in self._short_options:
                raise error.UnknownOption(first)
            return self._short_options[name]
        else:
            RuntimeError("Expected CLI-option name")

    def _parse_arguments(self, cli_arguments):
        """Parse raw command-line argument values."""

        values = []
        for argument, value in zip_longest(self._signature.arguments, cli_arguments):
            argument = argument or self._signature.vararg
            if argument is None:
                raise error.TooManyArguments()
            if argument.is_required() and value is None:
                raise error.ArgumentMissing(argument)
            if not argument.is_required() and value is None:
                values.append(argument.default)
                continue
            parse = self._get_argument_parser(argument)
            values.append(parse(value))
        return values

    @staticmethod
    def _make_generic_argument_parser(argument):
        """Generic argument parser factory."""

        def parser(value):
            """Generic argument parser."""
            try:
                return argument.type(value)
            except ValueError:
                raise error.InvalidArgumentValue(argument, value)

        return parser

    @staticmethod
    def _make_bool_argument_parser(argument):
        """Bool argument parser factory."""

        def parser(value):
            """Bool argument parser."""
            if value == argument.name:
                return True
            if value.lower() == 'true':
                return True
            if value.lower() == 'false':
                return False
            raise error.InvalidArgumentValue(argument, value)

        return parser

    @staticmethod
    def _get_argument_parser(argument):
        """Get a function parsing a raw argument value from the command-line."""
        if argument.type is bool:
            return Parser._make_bool_argument_parser(argument)
        return Parser._make_generic_argument_parser(argument)

    @staticmethod
    def _bool_option_parser(_):
        """Bool option parser factory."""
        return True

    @staticmethod
    def _make_generic_option_parser(option):
        """Generic option parser factory."""

        def parser(cli_arguments):
            """Generic option parser."""
            if not cli_arguments:
                raise error.MissingOptionValue(option)
            raw_value = cli_arguments.popleft()
            try:
                return option.type(raw_value)
            except ValueError:
                raise error.InvalidOptionValue(option, raw_value)

        return parser

    @staticmethod
    def _get_option_parser(option):
        """Get option value parser."""
        if option.type is bool:
            return Parser._bool_option_parser
        return Parser._make_generic_option_parser(option)
