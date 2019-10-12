"""Various handler-to-model bindings.

Description:
-----------

This module defines logic that binds different parts of
comandante API together to make it more convenient.
"""
from comandante.inner.helpers import getname
from comandante.inner.proxy import Proxy


class BoundCommand(Proxy):
    """Command bound to a particular handler.

    Represents a command accessed from a particular handler object
    (like `handler.command`). The command is usually just a wrapper
    around ordinary python function (or method) and thus it is not
    being automatically bound to the corresponding handler (like
    python's BoundMethods do). This class closes this gap.
    """

    def __init__(self, command, handler):
        """Initialize instance.

        :param command: cli-command (wrapper around python function)
        :param handler: cli-handler (a collection of commands)
        """
        super(BoundCommand, self).__init__(command)
        self._set('_handler', handler)

    def __getattr__(self, item):
        """Redirect attribute access to the underlying command."""
        return getattr(self.command, item)

    def __call__(self, *args, **kwargs):
        """Redirect function-like calls to the underlying command."""
        return self.command(self._handler, *args, **kwargs)

    def invoke(self, *args, **kwargs):
        """Invoke command using bound handler as a context and passing the given arguments and options."""
        return self.command.invoke(self._handler, *args, **kwargs)

    @property
    def command(self):
        """Get underlying bound command."""
        return self._target


class ImmutableDict(Proxy):
    def __init__(self, target):
        super(ImmutableDict, self).__init__(target)
        self._unsupport('clear', 'pop', 'popitem', 'update', 'setdefault')

    def __setitem__(self, key, value):
        raise TypeError('ImmutableDict does not support item assignment')

    def __delitem__(self, key):
        raise TypeError("ImmutableDict doesn't support item deletion")


class AttributeDict(ImmutableDict):
    """Immutable dict proxy with attribute-like access to its items."""

    def __getattr__(self, item):
        """Delegate attribute access to items contained by the underlying dict."""
        if hasattr(self._target, item):
            return getattr(self._target, item)
        if item in self._target:
            return self._target[item]
        error_pattern = "'{type}' object has no attribute '{name}'"
        error_message = error_pattern.format(type=getname(type(self._target)), name=item)
        raise AttributeError(error_message)
