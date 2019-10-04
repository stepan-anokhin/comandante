"""Comandante is a tool for building command-line interfaces in Python.

Description:
-----------

This package contains all the comandante definitions.

Please refer to comandante documentation for more details:
https://github.com/stepan-anokhin/comandante/blob/master/README.md
"""

from .decorators import option, command
from .errors import CliSyntaxException
from .handler import Handler
