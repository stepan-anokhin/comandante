"""Command-line argument types.

Description:
-----------

This module defines additional command-line
argument types (i.e. string-value parsers).
"""
from comandante.inner.helpers import getname


def choice(*options):
    """Choice (enum) cli-argument type."""

    def result(value):
        if value in options:
            return value
        raise ValueError("Invalid value: {value}".format(value=str(value)))

    result.__name__ = '|'.join(options)
    return result


def listof(value_type):
    """List of values."""

    def result_type(value):
        return list(map(value_type, value.split(',')))

    result_type.__name__ = "list-of({type})".format(type=getname(value_type))
    return result_type
