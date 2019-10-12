"""Python object proxy

Description:
-----------

This module provides a generic python
object proxy class.
"""
from comandante.inner.helpers import getname


class Proxy(object):
    """Generic python object proxy."""

    def _unsupport(self, *names):
        for name in names:
            pattern = "'{type}' does not support method '{name}'"
            message = pattern.format(type=getname(type(self)), name=name)

            def stub(*_args, **_kwargs):
                raise TypeError(message)

            stub.__name__ = name
            self._set(name, stub)

    def _set(self, name, value):
        """Set attribute on the proxy itself."""
        object.__setattr__(self, name, value)

    def __init__(self, target):
        self._set('_target', target)

    def __getattr__(self, item):
        """Delegate attribute access to the underlying object."""
        return getattr(self._target, item)

    def __setattr__(self, key, value):
        """Delegate attribute assign to the underlying object."""
        if hasattr(self._target, key):
            setattr(self._target, key, value)
        self._set(key, value)

    def __setitem__(self, key, value):
        self._target[key] = value

    def __getitem__(self, item):
        return self._target[item]

    def __len__(self):
        return len(self._target)

    def __delitem__(self, key):
        del self._target[key]

    def __str__(self):
        return str(self._target)

    def __repr__(self):
        return repr(self._target)

    def __call__(self, *args, **kwargs):
        return self._target(*args, **kwargs)

    def __iter__(self):
        return iter(self._target)

    def __next__(self):
        return next(self._target)

    def __bool__(self):
        return bool(self._target)

    def __hash__(self):
        return hash(self._target)

    def __eq__(self, other):
        return self._target == other

    def __ge__(self, other):
        return self._target >= other

    def __gt__(self, other):
        return self._target > other

    def __le__(self, other):
        return self._target <= other

    def __lt__(self, other):
        return self._target < other

    def __ne__(self, other):
        return self._target != other

    def __dir__(self):
        return dir(self._target)

    def __contains__(self, item):
        return item in self._target
