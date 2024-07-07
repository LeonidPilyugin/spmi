"""
.. module:: state.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class State(metaclass=ABCMeta):
    """Represents an immutable state."""

    @abstractmethod
    def full_string(self) -> str:
        """Returns full string describing this object.

        Returns:
            str.
        """
        raise NotImplementedError()

    @abstractmethod
    def short_string(self):
        """Returns a short string describing this object.

        Returns:
            str.
        """
        raise NotImplementedError()

    def dict(self) -> dict:
        """Converts object to dictionary.

        Returns:
            :obj:`dict`.

        Note:
            Equal to :fun:`dataclasses.asdict`.
        """
        return asdict(self)
