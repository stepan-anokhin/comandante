"""Terminal properties detection.

Description:
-----------

This module provides components to describe
and detect properties of terminal viewport
to which help the output will be printed.
"""

import os


class Terminal:
    """Terminal properties."""
    DEFAULT_MAX_COLS = 70
    DEFAULT_MIM_COLS = 30

    @staticmethod
    def detect(max_cols=DEFAULT_MAX_COLS, min_cols=DEFAULT_MIM_COLS):
        if hasattr(os, 'get_terminal_size'):
            cols, lines = os.get_terminal_size()
            cols = min(max_cols, max(min_cols, cols))
            return Terminal(cols=cols, lines=lines)
        return Terminal(cols=max_cols)

    def __init__(self, cols=DEFAULT_MAX_COLS, lines=1):
        self._cols = cols
        self._lines = lines

    @property
    def cols(self):
        return self._cols

    @property
    def lines(self):
        return self._lines
