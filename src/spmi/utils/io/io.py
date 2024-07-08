"""
.. module:: io.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import inspect
from abc import ABCMeta, abstractmethod
from pathlib import Path
from filelock import FileLock
from spmi.utils.load import load_module

class Io(metaclass=ABCMeta):
    """Formatted input and output."""

    def __init__(self, path: Path, encoding: str = "utf-8"):
        """Constructor.

        Args:
            path (:obj:`Path`): path to file
            encoding (str): encoding.
        """
        assert isinstance(path, Path)
        assert not path.exists() or path.is_file()
        assert isinstance(encoding, str)

        self.path = path
        self.encoding = encoding

    @abstractmethod
    def copy(self):
        """Return a copy."""
        raise NotImplementedError()

    @property
    def path(self) -> str:
        """str. Path"""
        return self._path

    @path.setter
    def path(self, value: Path):
        assert isinstance(value, Path)
        assert not value.exists() or value.is_file()

        self._path = value
        self._lock = FileLock(value.parent.joinpath(value.name + ".lock"))

    def lock(self):
        """Lock."""
        self._lock.lock()

    def acquire(self):
        """Acquire."""
        self._lock.acquire()

    @property
    def is_locked(self) -> bool:
        """bool. True if file is locked."""
        return self._lock.is_locked()

    def blocking_load(self) -> dict:
        """Blocking load.

        Returns:
            :obj:`dict`. File representation as dict.
        """
        with self._lock:
            result = self.load()
        return result

    def blocking_dump(self, data: dict):
        """Blocking dump.

        Args:
            data (:obj:`dict`): Dict to dump.
        """
        with self._lock:
            self.dump(data)

    @abstractmethod
    def load(self) -> dict:
        """Load.

        Returns:
            :obj:`dict`. File representation as dict.
        """
        raise NotImplementedError()

    @abstractmethod
    def dump(self, data: dict):
        """Dump.

        Args:
            data (:obj:`dict`): Dict to dump.
        """
        raise NotImplementedError()

    @staticmethod
    def get_io_suffix(suffix: str):
        """Return io class by suffix.

        Args:
            suffix (str): suffix of file.

        Returns:
            :obj:`class`. Io realisation.
        """
        suffix = suffix[1:]
        assert suffix not in ["io", "ioable"]

        module = load_module(
            f"__spmi_{suffix}_io_realisation",
            Path(__file__).parent.joinpath(f"ios/{suffix}io.py")
        )

        return list(filter(
            lambda x: inspect.isclass(x[1]) and issubclass(x[1], Io) and x[1] is not Io,
            inspect.getmembers(module)
        ))[0][1]

    @staticmethod
    def has_io(path: Path) -> bool:
        """Returns True if has loader for file by path.

        Args:
            path (:obj:`Path`): path.

        Returns:
            bool.
        """
        ios = Path(__file__).parent.joinpath("ios").iterdir()
        return f"{path.suffix[1:]}io" in [x.stem for x in ios]

    @staticmethod
    def get_io(path: Path):
        """Return io object by path.
        
        Args:
            path (:obj:`Path`): path

        Returns:
            :obj:`Io` class with this path.
        """
        return Io.get_io_suffix(path.suffix)(path)
