"""Provides :class:`Io`.
"""

from abc import ABCMeta, abstractmethod
from pathlib import Path
from filelock import FileLock
import spmi.utils.io.ios as ios_package
from spmi.utils.load import load_class_from_package
from spmi.utils.exception import SpmiException


def _get_lock(path):
    assert isinstance(path, Path)
    return path.parent.joinpath(path.name + ".lock")


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
            raise TypeError(f'path "{value}" must be a file')

        self._path = value
        self._lock = FileLock(_get_lock(value))

    def acquire(self):
        """Acquire lock.

        Raises:
            :class:`IoException`
        """
        try:
            self._lock.acquire()
        except Exception as e:
            raise IoException(f'Cannot acquire "{self.path}":\n{e}') from e

    def release(self):
        """Release lock.

        Raises:
            :class:`IoException`
        """
        try:
            self._lock.release()
        except Exception as e:
            raise IoException(f'Cannot acquire "{self.path}":\n{e}') from e

    def blocking_load(self):
        """Blocking load.

        Returns:
            :obj:`dict`. File representation as dict.

        Raises:
            :class:`IoException`
        """
        try:
            with self._lock:
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
            with self._lock:
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

    @abstractmethod
    def dump(self, data: dict):
        """Dump.

        Args:
            data (:obj:`dict`): Dictionary to dump.

        Raises:
            :class:`IoException`
        """

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

    @staticmethod
    def lock_exists(path):
        """Returns ``True`` if ``path`` has a lock file.

        Args:
            path (:obj:`pathlib.Path`): Path.

        Returns:
            :class:`TypeError`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a pathlib.Path, not {type(path)}")
        path = _get_lock(path)
        return path.exists() and path.is_file()

    @staticmethod
    def remove_lock(path):
        """Removes lock file by this path if it exists.

        Args:
            path (:obj:`pathlib.Path`): Locked path.

        Raises:
            :class:`TypeError`
            :class:`IoException`
        """
        if not Io.lock_exists(path):
            raise IoException(f'Lock file on "{path}" should exist')
        _get_lock(path).unlink()
