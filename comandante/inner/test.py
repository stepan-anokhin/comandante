import os
import sys
from contextlib import contextmanager

if sys.version_info > (3, 0):
    from io import StringIO
else:
    from cStringIO import StringIO


@contextmanager
def capture_output():
    """Capture stdout and stderr output."""
    old = (sys.stdout, sys.stderr)
    new = (StringIO(), StringIO())
    try:
        sys.stdout, sys.stderr = new
        yield new
    finally:
        sys.stdout, sys.stderr = old


@contextmanager
def suppress_output():
    """Suppress stdout and stderr output."""
    old = (sys.stdout, sys.stderr)
    ignore = open(os.devnull, 'w')
    try:
        sys.stdout, sys.stderr = ignore, ignore
        yield
    finally:
        sys.stdout, sys.stderr = old
        ignore.close()
