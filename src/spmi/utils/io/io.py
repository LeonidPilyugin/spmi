"""Provides :class:`Io`.
"""

import inspect
from abc import ABCMeta, abstractmethod
from pathlib import Path
from filelock import FileLock
from spmi.utils.load import load_module
from spmi.utils.exception import *

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

        Raises:
            :class:`TypeError`.
        """
        if not isinstance(encoding, str):
            raise TypeError(f"encoding must be a str, not {type(encoding)}")

        self.path = path
        self.encoding = encoding

    @abstractmethod
    def copy(self):
        """Return a copy."""
        raise NotImplementedError()

    @property
    def path(self):
        """:obj:`pathlib.Path`: Path to file.

        Raises:
            :class:`TypeError`.
        """
        return Path(self._path)

    @path.setter
    def path(self, value):
        if not isinstance(value, Path):
            raise TypeError(f"path must be a pathlib.Path, not {type(value)}")
        if value.exists() and not value.is_file():
            raise TypeError(f"path \"{path}\" must be a file")

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
    def has_io(suffix):
        """Returns ``True`` if has loader for file with suffix.

        Args:
            suffix (:obj:`str`): Suffix.

        Returns:
            :obj:`bool`.

        Raises:
            TypeError
        """
        if not isinstance(suffix, str):
            raise TypeError(f"suffix must be a str, not {type(suffix)}")

        if not suffix:
            return False
        if suffix[0] == ".":
            suffix = suffix[1:]

        ios = Path(__file__).parent.joinpath("ios").iterdir()

        return f"{suffix}io" in [x.stem for x in ios]

    @staticmethod
    def get_io(path):
        """Return io object by path.
        
        Args:
            path (:obj:`pathlib.Path`): Path

        Returns:
            :obj:`Io` class by this path.

        Raises:
            :class:`TypeError`
            :class:`ValueError`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a Path, not {type(suffix)}")
        if not Io.has_io(path.suffix):
            raise ValueError(f"Unsupported suffix: {path.suffix}")

        suffix = path.suffix[1:]

        module = load_module(
            f"__spmi_{suffix}_io_realisation",
            Path(__file__).parent.joinpath(f"ios/{suffix}io.py")
        )

        return list(filter(
            lambda x: inspect.isclass(x[1]) and issubclass(x[1], Io) and x[1] is not Io,
            inspect.getmembers(module)
        ))[0][1](path)

    @staticmethod
    def remove_lock(path):
        """Removes lock file by this path if it exists.

        Args:
            path (:obj:`pathlib.Path`): Locked path.

        Raises:
            :class:`TypeError`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a Path, not {type(suffix)}")
        path.parent.joinpath(path.name + ".lock").unlink()
