"""Provides :class:`Io`.
"""

import inspect
from abc import ABCMeta, abstractmethod
from pathlib import Path
from filelock import FileLock
from spmi.utils.load import load_module

class Io(metaclass=ABCMeta):
    """Formatted input and output.

    Each realisation of this class can load single file
    extention and defined in :mod:`ios` package in single file.
    Class and file name are based on file extention format.

    For example, :class:`ios.jsonio.Json` can load only ``.json``
    files.
    """

    def __init__(self, path, encoding="utf-8"):
        """
        Args:
            path (:obj:`pathlib.Path`): Path to file.
            encoding (:obj:`str`): Encoding.
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
    def path(self):
        """:obj:`pathlib.Path`: Path to file."""
        return Path(self._path)

    @path.setter
    def path(self, value):
        assert isinstance(value, Path)
        assert not value.exists() or value.is_file()

        self._path = value
        self._lock = FileLock(value.parent.joinpath(value.name + ".lock"))

    def acquire(self):
        """Acquire lock."""
        self._lock.acquire()

    def release(self):
        """Release lock."""
        self._lock.release()

    def blocking_load(self):
        """Blocking load.

        Returns:
            :obj:`dict`. File representation as dict.
        """
        with self._lock:
            result = self.load()
        return result

    def blocking_dump(self, data):
        """Blocking dump.

        Args:
            data (:obj:`dict`): Dictionary to dump.
        """
        with self._lock:
            self.dump(data)

    @abstractmethod
    def load(self):
        """Load.

        Returns:
            :obj:`dict`. File representation as dict.
        """
        raise NotImplementedError()

    @abstractmethod
    def dump(self, data: dict):
        """Dump.

        Args:
            data (:obj:`dict`): Dictionary to dump.
        """
        raise NotImplementedError()

    @staticmethod
    def get_io_suffix(suffix):
        """Return io class by suffix.

        Args:
            suffix (:obj:`str`): suffix of file.

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
    def has_io(path: Path):
        """Returns ``True`` if has loader for file by path.

        Args:
            path (:obj:`Path`): Path.

        Returns:
            :obj:`bool`.
        """
        ios = Path(__file__).parent.joinpath("ios").iterdir()
        return f"{path.suffix[1:]}io" in [x.stem for x in ios]

    @staticmethod
    def get_io(path):
        """Return io object by path.
        
        Args:
            path (:obj:`pathlib.Path`): Path

        Returns:
            :obj:`Io` class by this path.
        """
        return Io.get_io_suffix(path.suffix)(path)

    @staticmethod
    def remove_lock(path):
        """Removes lock file by this path if it exists.

        Args:
            path (:obj:`pathlib.Path`): Locked path.
        """
        assert isinstance(path, Path)
        path.parent.joinpath(path.name + ".lock").unlink()
