"""Internal helpers.

Description:
-----------

This module contains comandante helpers intended
for internal use only.
"""

import inspect
import itertools


def isblank(line):
    """Check if the line is blank"""
    return line.isspace() or len(line) == 0


def describe(o):
    """Describe object using its documentation.

    :param o: object to be described.
    :return: (brief, long) description pair
    """
    if inspect.getdoc(o) is None:
        return '', ''
    lines = inspect.getdoc(o).split('\n')
    brief = lines[0]
    descr = itertools.dropwhile(isblank, lines[1:])
    return brief, '\n'.join(descr)
