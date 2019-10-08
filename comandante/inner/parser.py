"""Command line argument parsing.

Description:
-----------

This module defines a `Parser` class which is responsible
for reading and interpreting command-line arguments according
to the command line description in terms of domain model.
"""

import itertools

from comandante.errors import CliSyntaxException
from comandante.inner.helpers import getname


class Parser:
    """Command-line arguments parser.

    The sole responsibility of the `Parser` is to take a command
    domain model in terms of options and arguments and then
    interpret command-line arguments accordingly.
    """

    def __init__(self, options, arguments, vararg):
        """Initialize instance.

        :param options: command options
        :param arguments: command arguments (order is essential)
        :param vararg: var-arg descriptor (could be `None`)
        """
        self._options = options
        self._arguments = tuple(arguments)
        self._vararg = vararg
        self._opt_names = {}
        self._opt_short_names = {}
        for option in options:
            self._opt_names[option.name] = option
            self._opt_short_names[option.short] = option

    # TODO: specify exact cli-arguments format
    # [command-name] [options] [arguments] [var-arg...]
    def parse(self, argv):
        """Parse command line arguments.

        :param argv: command line arguments
        :return: option and argument values
        """
        options, rest = self._parse_options(argv)
        arguments = self._parse_arguments(rest)
        return options, arguments

    def _parse_options(self, argv):
        """Parse options.

        :param argv: a list containing raw command-line arguments
        :return: a dict containing option values and remaining command-line arguments
        """
        options = {}
        remain = list(reversed(argv))
        while self._more_options(remain):
            name, value = self._parse_option(remain)
            if name in options:
                raise CliSyntaxException("Duplicated option: '{name}'".format(name=name))
            options[name] = value

        merged_options = self._default_options()
        merged_options.update(options)
        return merged_options, reversed(remain)

    def _default_options(self):
        result = {}
        for option in self._options:
            result[option.name] = option.default
        return result

    @staticmethod
    def _more_options(remain):
        """Check if the remaining cli-arguments contain options."""
        return len(remain) > 0 and (remain[-1].startswith('--') or remain[-1].startswith('-'))

    def _parse_option(self, remain):
        """Parse a single option from the remaining raw command-line arguments"""
        option = self._get_option(remain)
        value = self._parse_option_value(option, remain)
        return option.name, value

    def _get_option(self, remain):
        """Determine option from the remaining raw command-line arguments."""
        argument = remain.pop()
        if argument.startswith('--'):
            option_name = argument[2:]
            if option_name not in self._opt_names:
                raise CliSyntaxException("Unknown option: '{option}'".format(option=argument))
            return self._opt_names[option_name]
        elif argument.startswith('-'):
            option_name = argument[1:]
            if option_name not in self._opt_short_names:
                raise CliSyntaxException("Unknown option: '{option}'".format(option=argument))
            return self._opt_short_names[option_name]
        else:
            raise RuntimeError("Cannot read option. Remaining arguments: {args}".format(args=list(reversed(remain))))

    def _parse_option_value(self, option, remain):
        """Parse option value from the given raw cli-arguments stack."""
        parse = self._get_option_parser(option)
        return parse(remain)

    @staticmethod
    def _get_option_parser(option):
        """Get option value parser."""
        if option.type is bool:
            return lambda remain: True

        def parser(remain):
            """Generic option value parser."""
            if len(remain) == 0:
                raise CliSyntaxException("Option '{name}' is missing argument value".format(name=option.name))
            value = remain.pop()
            try:
                return option.type(value)
            except ValueError:
                pattern = "Invalid value format for option: '{name}'\nExpected type: {type}\nActual value: '{value}'"
                message = pattern.format(name=option.name, value=value, type=option.type.__name__)
                raise CliSyntaxException(message)

        return parser

    def _parse_arguments(self, remain):
        """Parse raw command-line argument values."""
        values = []
        for argument, value in itertools.zip_longest(self._arguments, remain):
            argument = argument or self._vararg
            if argument is None:
                raise CliSyntaxException("Too many arguments.")
            if argument.is_required() and value is None:
                raise CliSyntaxException("Required argument is not specified: '{name}'".format(name=argument.name))
            if not argument.is_required() and value is None:
                values.append(argument.default)
                continue
            parse = self._get_argument_parser(argument)
            values.append(parse(value))
        return values

    @staticmethod
    def _get_argument_parser(argument):
        """Get a function parsing a raw argument value from the command-line."""
        if argument.type is bool:
            return lambda value: value == argument.name

        def parser(value):
            """Parse argument value."""
            try:
                return argument.type(value)
            except ValueError as e:
                error_pattern = "Invalid value for argument '{name}' of type '{type}': '{value}'"
                error_message = error_pattern.format(name=argument.name, type=getname(argument.type), value=value)
                raise CliSyntaxException(error_message)

        return parser
