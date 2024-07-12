"""Provides :class:`PatternMatcher`.

Todo:
    Add regex pattern matcher.
"""

import re
from abc import ABCMeta, abstractmethod

class PatternMatcher(metaclass=ABCMeta):
    """Provides methods to match pattern strings."""

    @abstractmethod
    def is_pattern(self, string):
        """Returns ``True`` if ``string`` is pattern.

        Args:
            string (:obj:`str`): String to check.

        Returns:
            :obj:`bool`.
        """
        raise NotImplementedError()

    @abstractmethod
    def match(self, pattern, string):
        """Returns ``True`` if ``string`` matches ``pattern``.

        Args:
            pattern (:obj:`str`): Pattern.
            string (:obj:`str`): String.

        Returns:
            :obj:`bool`.
        """
        raise NotImplementedError()


class SimplePatternMatcher(PatternMatcher):
    """Simple pattern matcher."""
    def is_pattern(self, string):
        if not isinstance(string, str):
            raise TypeError(f"string must be a str, not {type(string)}")

        return True

    def match(self, pattern, string):
        if not isinstance(pattern, str):
            raise TypeError(f"pattern must be a str, not {type(pattern)}")
        if not isinstance(string, str):
            raise TypeError(f"string must be a str, not {type(string)}")

        return string == pattern

class RegexPatternMatcher(PatternMatcher):
    """Regex pattern matcher."""
    def is_pattern(self, string):
        if not isinstance(string, str):
            raise TypeError(f"string must be a str, not {type(string)}")
        try:
            re.compile(string)
            return True
        except Exception:
            return False

    def match(self, pattern, string):
        if not isinstance(pattern, str):
            raise TypeError(f"pattern must be a str, not {type(pattern)}")
        if not isinstance(string, str):
            raise TypeError(f"string must be a str, not {type(string)}")

        p = re.compile(pattern)

        return p.match(string)
