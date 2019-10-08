"""Various handler-to-model bindings.

Description:
-----------

This module defines logic that binds different parts of
comandante API together to make it more convenient.
"""
from comandante.inner.proxy import Proxy


class BoundCommand:
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
        self._command = command
        self._handler = handler

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
    def handler(self):
        """Handler to which the command is bound."""
        return self._handler

    @property
    def command(self):
        """Get underlying bound command."""
        return self._command


class CommandMethodDescriptor:
    """Command-as-an-attribute descriptor.

    Wrapper around cli-command defined as a Handler method.
    CommandMethodDescriptor carries out automatic handler-to-command binding when
    accessed as a handler's attribute.

    See https://docs.python.org/3/reference/datamodel.html#implementing-descriptors
    """

    def __init__(self, command):
        """Initialize instance.

        :param command: command to be wrapped around.
        """
        self._command = command

    def __get__(self, instance, owner):
        """Bind wrapped command to the handler instance when accessed as handler's attribute."""
        return BoundCommand(self._command, instance)

    def __getattr__(self, item):
        """Delegate attribute access to the wrapped cli-command."""
        return getattr(self._command, item)


class WithOptionsHandlerProxy(Proxy):
    """Wrapper setting cli-handler option values.

    HandlerProxy is used to temporary set handler option values.
    """

    def __init__(self, handler, options):
        """Initialize instance.

        :param handler: handler to wrap around.
        :param options: dict containing option values to be set.
        """
        super().__init__(handler)
        super().__setattr__('_options', options)

    def __getattr__(self, item):
        """Delegate attribute access to the underlying handler."""
        value = getattr(self._target, item)
        if type(value) is BoundCommand:
            return BoundCommand(value.command, self)
        return value

    @property
    def options(self):
        """Get options."""
        return self._options
