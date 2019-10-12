"""Command-line interface handler.

Description:
-----------

This module defines a core concept of comandante -
a command-line interface handler.
"""

from __future__ import print_function

import comandante.decorators as decor
from comandante.errors import UnknownCommand
from comandante.inner.bind import BoundCommand, ImmutableDict
from comandante.inner.helpers import describe, getname
from comandante.inner.model import Option, Command
from comandante.inner.output.help_writer import HelpWriter


class Handler(object):
    """Command-line interface handler.

    Handler represents a collection of cli-commands invoked by their names.
    Handler is defined as ordinary python class.

    Handler methods decorated with the `@comandante.decorators.command()`
    will be considered as a cli-tool commands.

    Handler's doc-string will be used by a cli help command.
    """

    def __init__(self, name=None):
        """Initialize instance.

        Among other things this constructor will walk through
        all existing methods and collect those marked as
        cli-commands.
        """
        self._name = name or getname(type(self)).lower()
        self._declared_commands = {}
        self._declared_options = {}
        self._short_options = set()
        self._brief, self._descr = self._describe()
        self._discover_commands()

    def _discover_commands(self):
        """Discover commands declared as class-methods."""
        for name in dir(self):
            value = getattr(self, name)
            if type(value) is Command:
                bound_command = BoundCommand(command=value.copy(), handler=self)
                setattr(self, name, bound_command)
                self.declare_command(bound_command.name, bound_command)

    def _describe(self):
        """Derive description from the docstring."""
        if type(self) is Handler:
            # ignore docstring from the generic handler
            return '', ''
        return describe(self)

    def invoke(self, argv, context=()):
        """Invoke cli-handler with the given raw command-line arguments."""
        if len(argv) == 0:
            self.help()
            return
        command_name, argv = argv[0], argv[1:]
        if command_name not in self._declared_commands:
            error_message = "Unknown command: '{name}'".format(name=' '.join(context + (command_name,)))
            print(error_message)
            self.help()
            raise UnknownCommand(error_message)

        command = self._declared_commands.get(command_name, self.help)
        return command.invoke(argv, context + (command_name,))

    @decor.command()
    def help(self, command=None, *subcommands):
        """Display help information

        With no <command_name> given, the synopsis and a
        list of commands are printed on the standard output.
        """
        if command is None:
            print(self.full_doc())
            return

        element = self
        context = [self.name]
        full_name = [command] + list(subcommands)
        for name in full_name:
            if name not in element.declared_commands:
                print("Unknown command: {name}".format(name=' '.join(full_name)))
                print(element.full_doc(full_name=context))
                return
            context.append(name)
            element = element.declared_commands[name]

        print(element.full_doc(full_name=context))

    @property
    def name(self):
        return self._name

    @property
    def brief(self):
        """Get brief handler description."""
        return self._brief

    @property
    def descr(self):
        """Get long handler description."""
        return self._descr

    def full_doc(self, full_name=None):
        """Get full documentation"""
        help_writer = HelpWriter()
        return help_writer.document_handler(self, full_name)

    def declare_command(self, name, handler):
        """Declare subcommand."""
        if name in self._declared_commands:
            raise RuntimeError("Duplicate command name: {name}".format(name=name))
        self._declared_commands[name] = handler
        handler.use_options(self.declared_options.values())

    def declare_option(self, name, short, type, default, descr=""):
        """Declare a new option.

        Option defined by this method will be available for
        all handler commands.

        :param name: option name
        :param short: option short name
        :param type: option type
        :param default: option default value
        :param descr: option description
        """
        if name in self.declared_options:
            raise RuntimeError("Duplicate option name: '--{name}'".format(name=name))
        if short in self._short_options:
            raise RuntimeError("Duplicate option name: '-{name}'".format(name=short))
        option = Option(name=name, short=short, type=type, default=default, descr=descr)
        self._declared_options[option.name] = option
        self._short_options.add(short)
        for command in self.declared_commands.values():
            command.use_option(option)

    def use_option(self, option):
        """Declare identical option."""
        self.declare_option(
            name=option.name,
            short=option.short,
            type=option.type,
            default=option.default,
            descr=option.descr)

    def use_options(self, options):
        """Declare options identical to provided."""
        for option in options:
            self.use_option(option)

    @property
    def declared_options(self):
        """Get declared options."""
        return ImmutableDict(self._declared_options)

    @property
    def declared_commands(self):
        """Get declared commands."""
        return ImmutableDict(self._declared_commands)

    def __getattr__(self, item):
        if item not in self._declared_commands:
            raise AttributeError("{type} object has no attribute {name}".format(type=type(self).__name__, name=item))
        return self._declared_commands[item]
