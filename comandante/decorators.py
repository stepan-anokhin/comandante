from comandante.inner.bind import CommandMethodDescriptor
from comandante.inner.model import Command


def command(name=None):
    def decorator(method):
        cmd = Command.from_function(method, name, is_method=True)
        return CommandMethodDescriptor(cmd)

    return decorator


def option(name, short, type, default):
    def decorator(cmd):
        cmd.declare_option(name=name, short=short, type=type, default=default)
        return cmd

    return decorator
