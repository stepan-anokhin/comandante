"""Comandante exception hierarchy.

Description:
-----------

This module contains classes representing errors related to
command line interface logic.
"""


class CliException(Exception):
    """Parent class for all comandante-related exceptions."""
    pass


class CliSyntaxException(CliException):
    """Indicates wrong command line syntax."""
    pass
