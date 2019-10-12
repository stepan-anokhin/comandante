"""Comandante public API decorators.

Description:
-----------

This module provides public decorators to associate
functions and handler methods with comandante domain
model.
"""

from comandante.inner.model import Command


def command(name=None):
    """Convert handler's method to the cli-command

    :param name: override command name
    :return: a handler cli-command decorator
    """

    def decorator(method):
        """Decorator converting method to cli-command."""
        return Command.from_function(method, name, is_method=True)

    return decorator


def option(name, short, type, default, descr=''):
    """Declare a new option for the given cli-command.

    :param name: option name
    :param short: option short name
    :param type: option type
    :param default: option default value
    :param descr: option description
    :return: a new decorator that will declare option for marked command
    """

    def decorator(element):
        """Decorator declaring a new option."""
        element.declare_option(name=name, short=short, type=type, default=default, descr=descr)
        return element

    return decorator


def signature(**types):
    """Set command argument types.

    :param types: mapping from arg name to arg type
    :return: a new decorator setting the arg types on Command
    """

    def decorator(element):
        """Decorator setting argument types."""
        element.signature.set_types(types)
        return element

    return decorator
