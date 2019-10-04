"""Command-line interface handler.

Description:
-----------

This module defines a core concept of comandante -
a command-line interface handler.
"""

import comandante.decorators as decor

from comandante.errors import CliSyntaxException
from comandante.inner.bind import BoundCommand, HandlerProxy
from comandante.inner.helpers import describe
from comandante.inner.model import Option


class Handler:
    """Command-line interface handler.

    Handler represents a collection of cli-commands invoked by their names.
    Handler is defined as ordinary python class.

    Handler methods decorated with the `@comandante.decorators.command()`
    will be considered as a cli-tool commands.

    Handler's doc-string will be used by a cli help command.
    """

    def __init__(self):
        """Initialize instance.

        Among other things this constructor will walk through
        all existing methods and collect those marked as
        cli-commands.
        """
        self._commands = {}
        self._declared_options = {}
        self._brief, self._descr = describe(self)
        self._options = {}
        for name in dir(self):
            attr = getattr(self, name)
            if type(attr) is BoundCommand:
                self._commands[name] = attr

    def invoke(self, *argv):
        """Invoke cli-handler with the given raw command-line arguments."""
        command_name, argv = argv[0], argv[1:]
        if command_name not in self._commands:
            self._print("Unknown command: '{name}'".format(name=command_name))
            self.help()
            return

        try:
            command = self._commands.get(command_name, self.help)
            command.invoke(*argv)
        except CliSyntaxException as e:
            self._print(str(e))
            self.help(command_name)

    @decor.command()
    def help(self, command=None):
        """A generic implementation of the `help` command.

        :param command: a command name to print help for.
        """
        self._print("from help. Command = {command}".format(command=repr(command)))  # TODO: implement

    def _print(self, *args):
        """Print output. Is convenient to intercept cli-handler's output."""
        print(*args)  # TODO: redirect output

    @property
    def brief(self):
        """Get brief handler description."""
        return self._brief

    @property
    def descr(self):
        """Get long handler description."""
        return self._descr

    def option(self, name, short, type, default):
        """Declare a new option.

        Option defined by this method will be available for
        all handler commands.

        :param name: option name
        :param short: option short name
        :param type: option type
        :param default: option default value
        """
        if name in self.declared_options:
            raise ValueError("Duplicate option name: '{name}'".format(name=name))
        option = Option(name=name, short=short, type=type, default=default)
        self._declared_options[option.name] = option

    @property
    def declared_options(self):
        """Get declared options."""
        return self._declared_options  # TODO: use immutable proxy

    def with_options(self, **options):
        """Get a proxy with options being temporary set to the given values.

        :param options: option values as kv-args
        """
        return HandlerProxy(self, options)
