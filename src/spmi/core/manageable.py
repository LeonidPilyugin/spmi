"""Provides :class:`Manageable`.
"""

import inspect
import shutil
from abc import abstractmethod, ABCMeta
from pathlib import Path
from spmi.utils.load import load_module
from spmi.utils.metadata import MetaData, MetaDataError, dontcheck
from spmi.utils.logger import Logger
from spmi.utils.io.io import Io
from spmi.utils.exception import SpmiException

class ManageableException(SpmiException):
    pass

def manageable(cls):
    """All manageables should be decorated with it.

    Note:
        Sets ``__old_init__`` attribute of class and
        ``_metadata`` and ``_metadata._outer_object`` of object.

    Raises:
        :class:`AttributeError`
    """
    def __new_init__(self, *args, data=None, meta=None, **kwargs):
        if not data:
            raise ValueError("Cannot create Manageable with empty data")

        self._logger = Logger(self.__class__.__name__)

        if "_metadata" not in dir(self):
            self._metadata = cls.MetaDataHelper(data=data, meta=meta, **kwargs)
            self._metadata._outer_object = self

        self._logger.debug(f"Creating \"{self.state.id}\"")

        if self.__old_init__:
            self.__old_init__(*args, data=data, meta=meta, **kwargs)

    if not "MetaDataHelper" in dir(cls):
        raise AttributeError("Each manageable must have a nested \"MetaDataHelper\" class")
    if not "FileSystemHelper" in dir(cls):
        raise AttributeError("Each manageable must have a nested \"FileSystemHelper\" class")

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
            """:obj:`str`. Prefered suffix.

            Raises:
                :class:`TypeError`
                :class:`ValueError`
            """
            if "prefered_suffix" in self._meta:
                return self._meta["prefered_suffix"]
            return self.data_path.suffix

        @prefered_suffix.setter
        def prefered_suffix(self, value):
            if not isinstance(value, str):
                raise TypeError(f"value must be a string, not {type(value)}")
            if not self.mutable:
                raise MetaDataError("Must be mutable")
            self._meta["prefered_suffix"] = value

        @property
        def type(self):
            """:obj:`str`. Type.

            Raises:
                :class:`ValueError`
                :class:`TypeError`
            """
            keys = list(self._data.keys())
            if len(keys) != 1:
                raise ValueError(f"Data dictionary must contain 1 element, not {len(keys)}")
            key = keys[0]
            if not isinstance(key, str):
                raise TypeError(f"Type of key in data dictionary must be str, not {type(key)}")

            return key

        @property
        def m_data(self):
            """:obj:`dict`. Manageable data."""
            return self._data[self.type]

        @property
        def id(self):
            """:obj:`str`. ID.

            Raises:
                :class:`KeyError`
            """
            return str(self.m_data["id"])

        @property
        def comment(self):
            """:obj:`str`. Comment.

            Raises:
                :class:`KeyError`
            """
            return str(self.m_data["comment"])

        @property
        def path(self):
            """:obj:`pathlib.Path`. Path.

            Raises:
                :class:`MetaDataError`
                :class:`TypeError`
            """
            if "path" in self._meta:
                res = self._meta["path"]
                if not res is None:
                    res = Path(res)
                return res
            return None

        @path.setter
        def path(self, value):
            if not self.mutable:
                raise MetaDataError("Must be mutable")
            if not (value is None or isinstance(value, Path)):
                raise TypeError(f"value must be None or Path, not {type(value)}")
            self._meta["path"] = value if value is None else str(value)


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

            Raises:
                :class:`TypeError`
                :class:`ManageableException`
                :class:`OSError`
            """
            if not isinstance(manageable, Manageable):
                raise TypeError(f"manageable must be a Manageable, not {type(manageable)}")
            if not isinstance(path, Path):
                raise TypeError(f"path must be a pathlib.Path, not {type(path)}")
            if path.exists():
                raise ManageableException(f"Path \"{path}\" should not exist")

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
            if not isinstance(manageable, Manageable):
                raise TypeError(f"manageable must be a Manageable, not {type(manageable)}")
            shutil.rmtree(manageable.state.path)

        @classmethod
        def is_correct_directory(cls, path):
            """Returns ``True`` if ``path`` may be a directory
            where :obj:`Manageable` registered.

            Args:
                path (:obj:`pathlib.Path`): Path to directory.

            Returns:
                :obj:`bool`.

            Raises:
                :class:`TypeError`
            """
            if not isinstance(path, Path):
                raise TypeError(f"path must be a [athlib.Path, not {type(path)}")

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

            Raises:
                :class:`TypeError`
                :class:`ManageableException`
            """
            if not isinstance(path, Path):
                raise TypeError(f"path must be a [athlib.Path, not {type(path)}")
            if not cls.is_correct_directory(path):
                raise ManageableException(f"Attempting to load from incorrect path \"{path}\"")

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

            Raises:
                :class:`TypeError`
                :class:`NotImplementedError`
            """
            if not isinstance(name, str):
                raise TypeError(f"name must be a str, not {type(name)}")

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

                    if len(classes) == 1:
                        return classes[0][1]

            raise NotImplementedError(f"Could not find manageable type \"{name}\"")

        @staticmethod
        def from_directory_unknown(path):
            """Loads registered manageable from directory.
            
            Args:
                path (:obj:`pathlib.Path`): Path to directory.

            Returns:
                :obj:`Manageable`.

            Raises:
                :class:`TypeError`
                :class:`ManageableException`
                :class:`NotImplementedError`
            """
            if not isinstance(path, Path):
                raise TypeError(f"path must be a pthlib.Path, not {type(path)}")
            if not Manageable.is_correct_directory(path):
                raise ManageableException(f"Cannot load Manageable from path \"{path}\"")

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

            Raises:
                :class:`TypeError`
                :class:`NotImplementedError`
                :class:`MetaDataError`
            """
            if not isinstance(path, Path):
                raise TypeError(f"path must be a pathlib.Path, not \"{type(path)}\"")

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
        """Starts this manageable.

        Raises:
            :class:`ManageableException`
        """
        raise NotImplementedError()

    @abstractmethod
    def term(self):
        """Terminate this manageable.

        Raises:
            :class:`ManageableException`
        """
        raise NotImplementedError()

    @abstractmethod
    def kill(self):
        """Kill this manageable.

        Raises:
            :class:`ManageableException`
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def active(self):
        """:obj:`bool`: ``True`` if active."""
        raise NotImplementedError()

    @property
    def state(self):
        """:obj:`Manageable.MetaDataHelper` state of this manageable."""
        return self._metadata.state

    def destruct(self):
        """Free all resources (filesystem too).
        
        Raises:
            :class:`ManageableException`
        """
        if self.active:
            raise ManageableException("Cannot destruct active manageable")
        self._logger.debug(f"Destructing \"{self.state.id}\"")
        type(self).FileSystemHelper.destruct(self)
        del self._metadata.meta_path
        del self._metadata.data_path

    def register(self, path):
        """Registers by path.

        To register a :class:`Manageable` means to create
        directory and save there meta and data files.

        Args:
            path (:obj:`pathlib.Path`): Path where manageable
                should be registered.

        Raises:
            :class:`ManageableException`
            :class:`TypeError`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a pathlib.Path, not {type(path)}")
        if self.registered:
            raise ManageableException("Already registered")
        self._logger.debug(f"Registering \"{self.state.id}\"")

        existed = path.exists()
        try:
            type(self).FileSystemHelper.register(self, path)
        except ManageableException:
            if not existed:
                shutil.rmtree(path)
            raise

    def status_string(self, align=0):
        """Returns status string of this manageable.

        Args:
            align (:obj:`int`): Align.
        """
        align = max(
            align,
            max(
                map(
                    lambda x: len(x),
                    [
                        "Active",
                        "Path",
                    ]
                )
            )
        )

        state = self.state
        result = ""
        result += f"{state.id} ({state.type}) - {state.comment}\n"
        result += f"{{:>{align}}}: {{:}}\n".format("Active", "\x1b[32;20mactive\x1b[0m" if self.active else "\x1b[31;20minactive\x1b[0m")
        result += f"{{:>{align}}}: \"{{:}}\"\n".format("Path", state.path)

        return result

    @property
    def registered(self):
        """:obj:`bool`: ``True`` if this manageable is registered."""
        return not self._metadata.meta_path is None

    def __enter__(self):
        self._metadata.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._metadata.__exit__(exc_type, exc_value, traceback)

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

        Raises:
            :class:`TypeError`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a pathlib.Path, not {type(path)}")
        return cls.FileSystemHelper.is_correct_directory(path)

    @classmethod
    def from_directory(cls, path):
        """Loads registered manageable from directory.

        Args:
            path (:obj:`pathlib.Path`): Path to directory.

        Returns:
            :obj:`Manageable`.

        Raises:
            :class:`TypeError`
            :class:`ManageableException`
            :class:`MetaDataError`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a pathlib.Path, not {type(path)}")

        return cls(**cls.FileSystemHelper.from_directory(path))

    @staticmethod
    def from_directory_unknown(path):
        """Loads registered manageable from directory.
        
        Args:
            path (:obj:`pathlib.Path`): Path to directory.

        Returns:
            :obj:`Manageable`.

        Raises:
            :class:`TypeError`
            :class:`ManageableException`
            :class:`MetaDataError`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a pathlib.Path, not {type(path)}")

        return Manageable.LoadHelper.from_directory_unknown(path)

    @staticmethod
    def from_descriptor(path):
        """Loads detected manageable from descriptor.

        Args:
            path (:obj:`pathlib.Path`): Path to descriptor.

        Returns:
            :obj:`Manageable`.

        Raises:
            :class:`TypeError`
            :class:`ManageableException`
            :class:`MetaDataError`
        """
        if not isinstance(path, Path):
            raise TypeError(f"path must be a pathlib.Path, not {type(path)}")

        return Manageable.LoadHelper.from_descriptor(path)
