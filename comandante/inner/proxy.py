"""Python object proxy

Description:
-----------

This module provides a generic python
object proxy class.
"""


class Proxy:
    """Generic python object proxy."""

    def __init__(self, target):
        super().__setattr__('_target', target)

    def __getattr__(self, item):
        """Delegate attribute access to the underlying object."""
        return getattr(self._target, item)

    def __setattr__(self, key, value):
        """Delegate attribute assign to the underlying object."""
        if hasattr(self._target, key):
            setattr(self._target, key, value)
        object.__setattr__(self, key, value)

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

    def __contains__(self, item):
        return item in self._target
