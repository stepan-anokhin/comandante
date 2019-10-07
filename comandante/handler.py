"""Command-line interface handler.

Description:
-----------

This module defines a core concept of comandante -
a command-line interface handler.
"""

import comandante.decorators as decor

from comandante.errors import CliSyntaxException
from comandante.inner.bind import BoundCommand, HandlerProxy
from comandante.inner.helpers import describe, getname
from comandante.inner.markup import TechWriter
from comandante.inner.model import Option


class Handler:
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
        self._commands = {}
        self._declared_options = {}
        self._brief, self._descr = self._describe()
        self._options = {}
        for name in dir(self):
            attr = getattr(self, name)
            if type(attr) is BoundCommand:
                self._commands[name] = attr

    def _describe(self):
        """Derive description from the docstring."""
        if type(self) is Handler:
            # ignore docstring from the generic handler
            return '', ''
        return describe(self)

    def invoke(self, *argv):
        """Invoke cli-handler with the given raw command-line arguments."""
        if len(argv) == 0:
            self.help()
            return
        command_name, argv = argv[0], argv[1:]
        if command_name not in self._commands:
            self._print("Unknown command: '{name}'".format(name=command_name))
            self.help()
            return

        try:
            command = self._commands.get(command_name, self.help)
            return command.invoke(*argv)
        except CliSyntaxException as e:
            self._print(str(e))
            self.help(command_name)

    @decor.command()
    def help(self, command=None):
        """Display help information about

        With no [command] given, the synopsis of the {name} and a
        list of commands are printed on the standard output.
        """
        if command is None:
            self._print(self.full_doc())
            return

        if command not in self._commands:
            self._print("Unknown command: {name}".format(name=command))
            self._print(self.full_doc())
            return

        self._print(self._commands[command].full_doc())

    def _help_command(self, command_name):
        """Print help for a particular command."""

    def _print(self, *args):
        """Print output. Is convenient to intercept cli-handler's output."""
        print(*args)  # TODO: redirect output

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

    def full_doc(self):
        """Get full documentation"""
        tech_writer = TechWriter()
        return tech_writer.document_handler(self)

    def subcommand(self, name, handler):
        """Declare subcommand."""
        if name in self._commands:
            raise RuntimeError("Duplicate command name: {name}".format(name=name))
        self._commands[name] = handler

    def option(self, name, short, type, default, descr=""):
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
            raise ValueError("Duplicate option name: '{name}'".format(name=name))
        option = Option(name=name, short=short, type=type, default=default, descr=descr)
        self._declared_options[option.name] = option

    @property
    def declared_options(self):
        """Get declared options."""
        return self._declared_options  # TODO: use immutable proxy

    @property
    def declared_commands(self):
        """Get declared commands."""
        return self._commands  # TODO: use immutable proxy

    def with_options(self, **options):
        """Get a proxy with options being temporary set to the given values.

        :param options: option values as kv-args
        """
        return HandlerProxy(self, options)

    @property
    def options(self):
        """Get option values."""
        return self._options

    def __getattr__(self, item):
        if item not in self._commands:
            raise AttributeError("{type} object has no attribute {name}".format(type=type(self).__name__, name=item))
        return self._commands[item]
