"""Internal helpers.

Description:
-----------

This module contains comandante helpers intended
for internal use only.
"""

import inspect

from comandante.inner.output.markup import Markup


def describe(o):
    """Describe object using its documentation.

    :param o: object to be described.
    :return: (brief, long) description pair
    """
    if inspect.getdoc(o) is None:
        return '', ''
    text = inspect.getdoc(o)
    parts = Markup.paragraph_break.split(text, maxsplit=1)
    brief = parts[0]
    descr = parts[1] if len(parts) == 2 else ''
    return brief, descr


def getname(o):
    """Get python object name."""
    if hasattr(o, '__name__') and o.__name__ is not None:
        return o.__name__
    raise ValueError("{object} doesn't have a name".format(object=str(o)))
