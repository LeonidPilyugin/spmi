"""
.. module:: ioable.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

from spmi.utils.io.io import Io

class Ioable:
    """Both io and dictionary."""
    def __init__(self, data: dict = None, io: Io = None):
        """Constructor.

        Args:
            data (:obj:`Union[dict, None]`): data. Empty if None.
            io (:obj:`Io`): Io.
        """
        self.io = io
        self.data = data if data else {}

    def load(self):
        """Load"""
        assert self.io
        self.data = self.io.load()

    def dump(self):
        """Dump"""
        assert self.io
        self.io.dump(self.data)

    def lock(self):
        """Lock"""
        assert self.io
        self.io.lock()

    def acquire(self):
        """Acquire"""
        assert self.io
        self.io.acquire()

    def is_locked(self) -> bool:
        """Returns True if is locked.

        Returns:
            bool.
        """
        assert self.io
        return self.io.is_lock()

    def blocking_load(self):
        """Blocking load."""
        assert self.io
        self.data = self.io.blocking_load()

    def blocking_dump(self):
        """Blocking dump."""
        assert self.io
        self.io.blocking_dump(self.data)
