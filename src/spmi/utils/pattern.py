"""
.. module:: pattern.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

from abc import ABCMeta, abstractmethod

class PatternMatcher(metaclass=ABCMeta):
    """Provides methods to match pattern"""

    @abstractmethod
    def is_pattern(self, string: str) -> bool:
        """Returns True if string is pattern.

        Args:
            string (str): string to check.

        Returns:
            bool.
        """
        raise NotImplementedError()

    @abstractmethod
    def match(self, pattern: str, string: str) -> bool:
        """Returns True if string matches pattern.

        Args:
            pattern (str): pattern.
            string (str): string.

        Returns:
            bool.
        """
        raise NotImplementedError()


class SimplePatternMatcher(PatternMatcher):
    """Simple pattern matcher."""
    def __init__(self):
        pass

    def is_pattern(self, string: str):
        return True

    def match(self, pattern: str, string: str) -> bool:
        return string == pattern
