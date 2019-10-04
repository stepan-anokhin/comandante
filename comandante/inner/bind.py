class BoundCommand:
    def __init__(self, command, handler):
        self._command = command
        self._handler = handler

    def __getattr__(self, item):
        return getattr(self.command, item)

    def __call__(self, *args, **kwargs):
        return self.command(self._handler, *args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self.command.invoke(self._handler, *args, **kwargs)

    @property
    def handler(self):
        return self._handler

    @property
    def command(self):
        return self._command


class CommandMethodDescriptor:
    def __init__(self, command):
        self._command = command

    def __get__(self, instance, owner):
        return BoundCommand(self._command, instance)

    def __getattr__(self, item):
        return getattr(self._command, item)


class HandlerProxy:
    def __init__(self, handler, options):
        self._handler = handler
        self._options = options

    def __getattr__(self, item):
        value = getattr(self._handler, item)
        if type(value) is BoundCommand:
            return BoundCommand(value.command, self)
        return value

    @property
    def options(self):
        return self._options
