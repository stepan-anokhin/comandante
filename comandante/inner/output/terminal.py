"""Terminal properties detection.

Description:
-----------

This module provides components to describe
and detect properties of terminal viewport
to which help the output will be printed.
"""

import platform
import subprocess


class Terminal:
    """Terminal properties."""
    PREFERRED_WIDTH = 70

    @staticmethod
    def detect(max_width=PREFERRED_WIDTH):
        system = platform.system()
        if system == 'Linux':
            width, height = Terminal._terminal_geometry_linux(default_width=max_width)
            return Terminal(width=min(width, max_width), height=height)
        return Terminal(width=max_width)

    @staticmethod
    def _terminal_geometry_linux(default_width):
        try:
            output = subprocess.check_output(['stty', 'size'], stderr=False)
            height, width = tuple(map(int, output.split()))
            return width, height
        except (OSError, subprocess.CalledProcessError):
            return default_width, 1

    def __init__(self, width=60, height=1, ):
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height
