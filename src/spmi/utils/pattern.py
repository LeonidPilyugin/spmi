"""Provides :class:`PatternMatcher`.
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
        if not isinstance(string, str):
            raise TypeError(f"string must be a str, not {type(string)}")

    @abstractmethod
    def match(self, pattern, string):
        """Returns ``True`` if ``string`` matches ``pattern``.

        Args:
            pattern (:obj:`str`): Pattern.
            string (:obj:`str`): String.

        Returns:
            :obj:`bool`.

        Raises:
            :obj:`TypeError`
            :obj:`ValueError`
        """
        if not self.is_pattern(pattern):
            raise ValueError("pattern must be a pattern string")
        if not isinstance(string, str):
            raise TypeError(f"string must be a str, not {type(string)}")


class SimplePatternMatcher(PatternMatcher):
    """Simple pattern matcher."""
    def is_pattern(self, string):
        super().is_pattern(string)
        return True

    def match(self, pattern, string):
        super().match(pattern, string)
        return string == pattern

class RegexPatternMatcher(PatternMatcher):
    """Regex pattern matcher."""
    def is_pattern(self, string):
        super().is_pattern(string)
        try:
            re.compile(string)
            return True
        except Exception:
            return False

    def match(self, pattern, string):
        super().match(pattern, string)
        p = re.compile(pattern)
        return p.match(string)
