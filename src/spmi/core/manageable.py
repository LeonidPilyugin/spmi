"""Provides :class:`Manageable`.
"""

import inspect
import shutil
from abc import abstractmethod, ABCMeta
from pathlib import Path
from spmi.utils.load import load_module
from spmi.utils.metadata import MetaData
from spmi.utils.logger import Logger
from spmi.utils.io.io import Io

def manageable(cls):
    """All manageables should be decorated with it.

    Note:
        Sets ``__old_init__`` attribute of class and
        ``_metadata`` and ``_metadata._outer_object`` of object.
    """
    def __new_init__(self, *args, data=None, meta=None, **kwargs):
        assert data

        self._logger = Logger(self.__class__.__name__)

        if "_metadata" not in dir(self):
            self._metadata = cls.MetaDataHelper(data=data, meta=meta, **kwargs)
            self._metadata._outer_object = self

        self._logger.debug(f"Creating \"{self.state.id}\"")

        if self.__old_init__:
            self.__old_init__(*args, data=data, meta=meta, **kwargs)

    assert "MetaDataHelper" in dir(cls)
    assert "FileSystemHelper" in dir(cls)

    cls.FileSystemHelper._outer_class = cls

    cls.__old_init__ = cls.__init__
    cls.__init__ = __new_init__
    return cls


@manageable
class Manageable(metaclass=ABCMeta):
    """This class describes object which can be managed by SPMI.

    Any realisation should be defined in :py:mod:`spmi.core.manageables`
    package in own file and decorated with :func:`manageable`. Its name
    should be written in PascalCase and ended with "Manageable".
    """
    class MetaDataHelper(MetaData):
        @property
        def prefered_suffix(self):
            """:obj:`str`. Prefered suffix."""
            if "prefered_suffix" in self._meta:
                return self._meta["prefered_suffix"]
            assert self.data_path
            return self.data_path.suffix

        @prefered_suffix.setter
        def prefered_suffix(self, value):
            assert isinstance(value, str)
            assert self.mutable
            self._meta["prefered_suffix"] = value

        @property
        def type(self):
            """:obj:`str`. Type"""
            keys = list(self._data.keys())
            assert len(keys) == 1
            key = keys[0]
            assert isinstance(key, str)

            return key

        @property
        def m_data(self):
            """:obj:`dict`. Manageable data."""
            return self._data[self.type]

        @property
        def id(self):
            """:obj:`str`. ID."""
            return str(self.m_data["id"])

        @property
        def path(self):
            """:obj:`pathlib.Path`. Path"""
            if "path" in self._meta:
                res = self._meta["path"]
                if not res is None:
                    res = Path(res)
                return res
            return None

        @path.setter
        def path(self, value):
            assert value is None or isinstance(value, Path)
            assert self.mutable
            self._meta["path"] = value if value is None else str(value)

        def __str__(self):
            return rf"""{self.type} Manageable:
id: {self.id}
path: {self.path}
"""

    class FileSystemHelper:
        """Contains methods to work with filesystem."""

        DATA_FILENAME = "data"
        """:obj:`str`: name of data file (without extention)"""
        META_FILENAME = "meta"
        """:obj:`str`: name of meta file (without extention)"""

        @staticmethod
        def data_pathes(path):
            """Return all potential data pathes.

            Args:
                path (:obj:`pathlib.Path`): Directory path.

            Returns:
                :obj:`list` of :obj:`pathlib.Path`.
            """
            return list(
                filter(
                    lambda x: ".lock" not in x.suffix,
                    path.rglob(Manageable.FileSystemHelper.DATA_FILENAME + ".*")
                )
            )

        @staticmethod
        def meta_pathes(path):
            """Return all potential meta pathes.

            Args:
                path (:obj:`pathlib.Path`): Directory path.

            Returns:
                :obj:`list` of :obj:`pathlib.Path`.
            """
            return list(
                filter(
                    lambda x: ".lock" not in x.suffix,
                    path.rglob(Manageable.FileSystemHelper.META_FILENAME + ".*")
                )
            )

        @staticmethod
        def data_path(path):
            """Returns path to data file.

            Args:
                path (:obj:`pathlib.Path`): Directory path.

            Returns:
                :obj:`pathlib.Path`.
            """
            return Manageable.FileSystemHelper.data_pathes(path)[0]

        @staticmethod
        def meta_path(path):
            """Returns path to meta file.

            Args:
                path (:obj:`pathlib.Path`): Directory path.

            Returns:
                :obj:`pathlib.Path`.
            """
            return Manageable.FileSystemHelper.meta_pathes(path)[0]

        @classmethod
        def register(cls, manageable, path):
            """Registeres manageable by path.

            Args:
                manageable (:obj:`Manageable`): Manageable to register.
                path (:obj:`pathlib.Path`): Path to use.
            """
            assert isinstance(manageable, Manageable)
            assert isinstance(path, Path)
            assert not path.exists()

            path.mkdir()
            manageable._metadata.path = path

            manageable._metadata.data_path = path.joinpath(
                Path(Manageable.FileSystemHelper.DATA_FILENAME).with_suffix(
                    manageable.state.prefered_suffix
                )
            )
            manageable._metadata.meta_path = path.joinpath(
                Path(Manageable.FileSystemHelper.META_FILENAME).with_suffix(
                    manageable.state.prefered_suffix
                )
            )

            manageable._metadata.dump()

        @classmethod
        def destruct(cls, manageable):
            """Destructs manageable.

            Args:
                manageable (:obj:`Manageable`): Manageable to destruct.
            """
            assert isinstance(manageable, Manageable)
            shutil.rmtree(manageable.state.path)

        @classmethod
        def is_correct_directory(cls, path):
            """Returns ``True`` if ``path`` may be a directory
            where :obj:`Manageable` registered.

            Args:
                path (:obj:`pathlib.Path`): Path to directory.

            Returns:
                :obj:`bool`.
            """
            assert isinstance(path, Path)

            try:
                data_pathes = cls.data_pathes(path)
                meta_pathes = cls.meta_pathes(path)
                data_path = cls.data_path(path)
                meta_path = cls.meta_path(path)
                return all([
                    path.exists(),
                    path.is_dir(),
                    len(data_pathes) == 1,
                    len(meta_pathes) == 1,
                    data_path.exists(),
                    meta_path.exists(),
                    data_path.is_file(),
                    meta_path.is_file(),
                    data_path.suffix == meta_path.suffix,
                    cls._outer_class.MetaDataHelper.is_correct_meta_data(
                        data=data_path,
                        meta=meta_path
                    ),
                ])
            except Exception:
                return False

        @classmethod
        def from_directory(cls, path):
            """Returns keyword arguments to create :obj:`Manageable` object.

            Args:
                path (:obj:`pathlib.Path`): Path to directory.

            Returns:
                :obj:`dict`: Kwargs.
            """
            assert isinstance(path, Path)
            assert cls.is_correct_directory(path)

            return {
                "data": cls.data_path(path),
                "meta": cls.meta_path(path),
            }

    class LoadHelper:
        """Abstract load helper."""

        @staticmethod
        def get_class_name(string) -> str:
            """Converts ``string`` to class name.

            Args:
                string (:obj:`str`): String.

            Returns:
                str.
            """
            return "".join([x.capitalize() for x in string.split()]) + "Manageable"

        @staticmethod
        def load_manageable_class(name):
            """Loads manageable class by name.

            Args:
                name (:obj:`str`): Classname.

            Returns:
                :obj:`class`.
            """
            assert isinstance(name, str)

            for path in Path(__file__).parent.joinpath("manageables").iterdir():
                if path.is_file():
                    module_name = f"__manageable_realisation_{path.stem}"
                    module = load_module(module_name, path)

                    classes = inspect.getmembers(module)
                    classes = list(
                        filter(
                            lambda x: x[0] == Manageable.LoadHelper.get_class_name(name),
                            inspect.getmembers(module)
                        )
                    )

                    if len(classes) >= 1:
                        assert len(classes) == 1
                        return classes[0][1]

            raise NotImplementedError()

        @staticmethod
        def from_directory_unknown(path):
            """Loads registered manageable from directory.
            
            Args:
                path (:obj:`pathlib.Path`): Path to directory.

            Returns:
                :obj:`Manageable`.
            """
            assert isinstance(path, Path)
            assert Manageable.is_correct_directory(path)

            data_path = Manageable.FileSystemHelper.data_path(path)
            meta_path = Manageable.FileSystemHelper.meta_path(path)

            metadata = Manageable.MetaDataHelper(
                data=Manageable.FileSystemHelper.data_path(path),
                meta=Manageable.FileSystemHelper.meta_path(path)
            )

            return Manageable.LoadHelper.load_manageable_class(metadata.type)(
                data=data_path, meta=meta_path
            )

        @staticmethod
        def from_descriptor(path):
            """Loads detected manageable from descriptor.

            Args:
                path (:obj:`pathlib.Path`): Path to descriptor.

            Returns:
                :obj:`Manageable`.
            """
            assert isinstance(path, Path)

            metadata = Manageable.MetaDataHelper(
                data=path
            )

            manageable = Manageable.LoadHelper.load_manageable_class(metadata.type.capitalize())(
                data=path
            )

            Io.remove_lock(path)

            return manageable


    @abstractmethod
    def __init__(self, data=None, meta=None):
        """
        Args:
            data (:obj:`Union[dict, pathlib.Path, None]`): Data.
            meta (:obj:`Union[dict, pathlib.Path, None]`): Meta.
        """

    @abstractmethod
    def start(self):
        """Starts this manageable."""
        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        """Stops this manageable."""
        raise NotImplementedError()

    @property
    def state(self):
        """:obj:`Manageable.MetaDataHelper` state of this manageable."""
        return self._metadata.state

    def destruct(self):
        """Free all resources (filesystem too)."""
        self._logger.debug(f"Destructing \"{self.state.id}\"")
        type(self).FileSystemHelper.destruct(self)

    def register(self, path):
        """Registers by path.

        To register a :class:`Manageable` means to create
        directory and save there meta and data files.

        Args:
            path (:obj:`pathlib.Path`): Path where manageable
                should be registered.
        """
        assert not self.registered
        assert isinstance(path, Path)
        self._logger.debug(f"Registering \"{self.state.id}\"")
        type(self).FileSystemHelper.register(self, path)

    @property
    def registered(self):
        """:obj:`bool`: ``True`` if this manageable is registered."""
        return not self._metadata.meta_path is None

    def finish(self):
        """Dumps metadata."""
        assert self.registered
        self._logger.debug(f"Saving \"{self.state.id}\"")
        self._metadata.blocking_dump()

    @classmethod
    def is_correct_meta_data(cls, data, meta=None):
        """Returns ``True`` if ``meta`` and ``data``
        may be :class:`Manageable`'s meta and data.

        Args:
            data (:obj:`Union[dict, pathlib.Path]`): Data.
            meta (:obj:`Uinon[dict, pathlib.Path, None]`): Meta.

        Returns:
            :obj:`bool`.
        """
        return cls.MetaDataHelper.is_correct_meta_data(data=data, meta=meta)

    @classmethod
    def is_correct_directory(cls, path):
        """Returns ``True`` if this manageable is registered.

        Args:
            path (:obj:`pathlib.Path`): Path to directory.

        Returns:
            :obj:`bool`.
        """
        assert isinstance(path, Path)
        return cls.FileSystemHelper.is_correct_directory(path)

    @classmethod
    def from_directory(cls, path):
        """Loads registered manageable from directory.

        Args:
            path (:obj:`pathlib.Path`): Path to directory.

        Returns:
            :obj:`Manageable`.
        """
        assert isinstance(path, Path)
        assert cls.is_correct_directory(path)
        return cls(**cls.FileSystemHelper.from_directory(path))

    @staticmethod
    def from_directory_unknown(path):
        """Loads registered manageable from directory.
        
        Args:
            path (:obj:`pathlib.Path`): Path to directory.

        Returns:
            :obj:`Manageable`.
        """
        assert isinstance(path, Path)
        return Manageable.LoadHelper.from_directory_unknown(path)

    @staticmethod
    def from_descriptor(path):
        """Loads detected manageable from descriptor.

        Args:
            path (:obj:`pathlib.Path`): Path to descriptor.

        Returns:
            :obj:`Manageable`.
        """
        assert isinstance(path, Path)
        return Manageable.LoadHelper.from_descriptor(path)
