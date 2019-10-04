import comandante.decorators as decor

from comandante.errors import CliSyntaxException
from comandante.inner.bind import BoundCommand, HandlerProxy
from comandante.inner.helpers import describe
from comandante.inner.model import Option


class Handler:
    def __init__(self):
        self._commands = {}
        self._declared_options = {}
        self._brief, self._descr = describe(self)
        self._options = {}
        for name in dir(self):
            attr = getattr(self, name)
            if type(attr) is BoundCommand:
                self._commands[name] = attr

    def invoke(self, *argv):
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
        self._print("from help. Command = {command}".format(command=repr(command)))

    def _print(self, *args):
        print(*args)

    @property
    def brief(self):
        return self._brief

    @property
    def descr(self):
        return self._descr

    def option(self, name, short, type, default):
        if name in self.declared_options:
            raise ValueError("Duplicate option name: '{name}'".format(name=name))
        option = Option(name=name, short=short, type=type, default=default)
        self._declared_options[option.name] = option

    @property
    def declared_options(self):
        return self._declared_options  # TODO: use immutable proxy

    def with_options(self, **options):
        return HandlerProxy(self, options)
