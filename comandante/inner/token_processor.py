"""Pattern-based text processing.

Description:
-----------

This module contains `TokenProcessor` class
which provides simple token-based model for
text transformation.
"""

import re


class TokenProcessor:
    """Simple pattern-based text transformer."""

    def __init__(self, **tokens):
        self._rules = {}
        token_patterns = []
        for name, definition in tokens.items():
            pattern, rule = definition
            token_patterns.append("(?P<{name}>{pattern})".format(name=name, pattern=pattern))
            self._rules[name] = rule
        self._pattern = re.compile('|'.join(token_patterns))

    @staticmethod
    def _unpack(token):
        """Get rule name and matched text."""
        for name, matched_text in token.groupdict().items():
            if matched_text is not None:
                return name, matched_text
        raise ValueError("Invalid token.")

    def _process_token(self, token):
        """Get token text transformed according the rules."""
        name, matched_text = self._unpack(token)
        if name not in self._rules:
            raise RuntimeError("Undefined rule: {name}".format(name=name))
        rule = self._rules[name]
        return rule(matched_text)

    def process(self, text):
        """Apply rules to the given text."""
        last_end = 0
        chunks = []
        for token in self._pattern.finditer(text):
            interval = text[last_end:token.start()]
            chunk = self._process_token(token)
            chunks.append(interval)
            chunks.append(chunk)
            last_end = token.end()
        ending = text[last_end:]
        chunks.append(ending)
        return ''.join(chunks)
