"""Provides :class:`Io`.
"""

import os
import fcntl
from abc import ABCMeta, abstractmethod
from pathlib import Path
import spmi.utils.io.ios as ios_package
from spmi.utils.load import load_class_from_package
from spmi.utils.exception import SpmiException


class IoException(SpmiException):
    pass


class Io(metaclass=ABCMeta):
    """Formatted input and output.

    Each realisation of this class can load single file
    extention and defined in :mod:`ios` package in single file.
    Class and file name are based on file extention format.

    For example, :class:`ios.jsonio.Json` can load only ``.json``
    files.
    """

    def __init__(self, path):
        """
        Args:
            path (:obj:`pathlib.Path`): Path to file.

        Raises:
            :class:`TypeError`.
        """
        self.path = path
        self._fd = None

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
        return self._path

    @path.setter
    def path(self, value):
        if not isinstance(value, Path):
            raise TypeError(f"path must be a pathlib.Path, not {type(value)}")
        if value.exists() and not value.is_file():
            raise TypeError(f'path "{value}" must be a file')

        self._path = value

    def blocking_load(self):
        """Blocking load.

        Returns:
            :obj:`dict`. File representation as dict.

        Raises:
            :class:`IoException`
        """
        try:
            with self:
                result = self.load()
            return result
        except IoException:
            raise
        except Exception as e:
            raise IoException(
                f'Cannot process blocking load from "{self.path}":\n{e}'
            ) from e

    def blocking_dump(self, data):
        """Blocking dump.

        Args:
            data (:obj:`dict`): Dictionary to dump.

        Raises:
            :class:`IoException`
        """
        try:
            with self:
                self.dump(data)
        except IoException:
            raise
        except Exception as e:
            raise IoException(
                f'Cannot process blocking load from "{self.path}":\n{e}'
            ) from e

    @abstractmethod
    def load(self):
        """Load.

        Returns:
            :obj:`dict`. File representation as dict.

        Raises:
            :class:`IoException`
        """
        if not self._fd:
            raise IoException("Should be called inside \"with\" statement")
        self._fd.seek(0)

    @abstractmethod
    def dump(self, data: dict):
        """Dump.

        Args:
            data (:obj:`dict`): Dictionary to dump.

        Raises:
            :class:`IoException`
        """
        if not self._fd:
            raise IoException("Should be called inside \"with\" statement")
        self._fd.seek(0)
        self._fd.truncate(0)

    def __enter__(self):
        if not self._fd is None:
            raise IoException("Already inside \"with\" statement")
        self.path.touch()
        self._fd = open(self.path, "r+")
        fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX)

    def __exit__(self, exc_type, exc_value, traceback):
        assert not self._fd is None
        fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
        self._fd.close()
        self._fd = None

    @staticmethod
    def has_io(suffix):
        """Returns ``True`` if has loader for file with suffix.

        Args:
            suffix (:obj:`str`): Suffix.

        Returns:
            :obj:`bool`.

        Raises:
            :class:`TypeError`
            :class:`ValueError`
        """
        if not isinstance(suffix, str):
            raise TypeError(f"suffix must be a str, not {type(suffix)}")
        if not suffix:
            return False
        if not suffix.startswith("."):
            raise ValueError("suffix must be a return of pathlib.Path.suffix")

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
            :class:`IoException`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a Path, not {type(path)}")
        if not Io.has_io(path.suffix):
            raise IoException(f"Unsupported suffix: {path.suffix}")

        try:
            cls = load_class_from_package(
                f"{path.suffix[1:].capitalize()}Io", ios_package
            )
            return cls(path)
        except NotImplementedError as e:
            raise IoException(f"Unsupported suffix: {path.suffix} ({e})") from e
