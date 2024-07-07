"""
.. module:: manageable.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import inspect
import shutil
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from pathlib import Path
from spmi.utils.io.io import Io
from spmi.utils.io.ioable import Ioable
from spmi.utils.state import State
from spmi.utils.load import load_module

@dataclass(frozen=True)
class ManageableState(State):
    """Class containing immutable state of Manageable.

    Args:
        id (str): Unique identificator.
        is_active (bool): True, if manageable is active.
        path (str): Absolute path to manageable directory.
        preferred_suffix (str): Preferred suffix for data files.
    """
    id: str
    type: str
    is_active: bool
    path: str
    prefered_suffix: str

    def short_string(self) -> str:
        return f"{self.type.capitalize()} manageable object {self.id}"

    def full_string(self) -> str:
        return rf"""{self.id}
    type: {self.type}
    is active: {self.is_active}
    path: {self.path}
    preferred suffix: {self.prefered_suffix}
        """

def manageable(cls):
    """Manageable decorator. All manageables should be decoratet with it."""
    def __new_init__(self, *args, data=None, meta=None, **kwargs):
        assert data

        self._metadata = cls.MetaDataHelper(data=data, meta=meta, **kwargs)

        if self.__old_init__:
            self.__old_init__(*args, data=data, meta=meta, **kwargs)

    assert "MetaDataHelper" in dir(cls)
    assert "FileSystemHelper" in dir(cls)

    cls.__old_init__ = cls.__init__
    cls.__init__ = __new_init__
    return cls


@manageable
class Manageable(metaclass=ABCMeta):
    """This class describes object which can be managed.
    
    """
    class MetaDataHelper:
        """Provides access to meta and data."""
        def __init__(
            self,
            data: Ioable | dict | Path | None,
            meta: Ioable | dict | Path | None = None,
        ):
            """Constructor.

            Args:
                data (:obj:`Union[Ioable, dict]`): data.
                meta (:obj:`Union[Ioable, dict]`): meta.
                prefered_suffix (str): preferred suffix.
            """
            def load(value) -> Ioable:
                assert isinstance(value, (Ioable, dict, Path)) or value is None
                if isinstance(value, Ioable):
                    return value
                if isinstance(value, Path):
                    io = Ioable(io=Io.get_io(value))
                    io.blocking_load()
                    return io
                return Ioable(data=value)

            self._data = load(data)
            self._meta = load(meta)

            if self._data.io:
                self.prefered_suffix = self._data.io.path.suffix
            if "is_active" not in self._meta.data:
                self.is_active = False
            if "path" not in self._meta.data:
                self.path = None

            assert all([
                "prefered_suffix" in self._meta.data,
                len(self._data.data) == 1,
                isinstance(list(self._data.data.values())[0], dict),
                "id" in list(self._data.data.values())[0],
                "is_active" in self._meta.data,
                "path" in self._meta.data,
            ])

        @property
        def prefered_suffix(self) -> str:
            """str. Prefered suffix."""
            return self._meta.data["prefered_suffix"]

        @prefered_suffix.setter
        def prefered_suffix(self, value: str):
            assert isinstance(value, str)
            self._meta.data["prefered_suffix"] = value

        @property
        def id(self) -> str:
            """str. Id."""
            return list(self._data.data.values())[0]["id"]

        @property
        def type(self) -> str:
            """str. Type"""
            return list(self._data.data.keys())[0]

        @property
        def is_active(self) -> bool:
            """bool. True, if is active."""
            return self._meta.data["is_active"]

        @is_active.setter
        def is_active(self, value: bool):
            assert isinstance(value, bool)
            self._meta.data["is_active"] = value

        @property
        def path(self) -> Path:
            """:obj:`Path`. Path"""
            res = self._meta.data["path"]
            return res if not res else Path(res)

        @path.setter
        def path(self, value: Path):
            assert value is None or isinstance(value, Path)
            self._meta.data["path"] = value if value is None else str(value)

        @path.setter
        def path_setter(self, value: Path):
            assert value is None or all([
                isinstance(value, Path),
                value.exists(),
                value.is_dir(),
            ])
            self._meta.data["path"] = value or str(value)

        @property
        def state(self) -> ManageableState:
            """:obj:`ManageableState` Copy to immutable state."""
            return ManageableState(
                is_active=self.is_active,
                id=self.id,
                prefered_suffix=self.prefered_suffix,
                path=self.path,
                type=self.type,
            )

        def set_path(self, data_path: Path, meta_path: Path):
            """Set data and meta pathes"""
            assert isinstance(data_path, Path)
            assert isinstance(meta_path, Path)
            assert data_path.suffix == self.prefered_suffix
            assert meta_path.suffix == self.prefered_suffix

            self._data.io = Io.get_io(data_path)
            self._meta.io = Io.get_io(meta_path)

        def load(self):
            """Load meta and data."""
            assert self._data.io and self._meta.io
            self._data.load()
            self._meta.load()

        def dump(self):
            """Dump meta and data."""
            assert self._data.io and self._meta.io
            self._data.dump()
            self._meta.dump()

        def lock(self):
            """Lock meta and data."""
            assert self._data.io and self._meta.io
            self._data.lock()
            self._meta.lock()

        def acquire(self):
            """Acquire meta and data."""
            assert self._data.io and self._meta.io
            self._data.acquire()
            self._meta.acquire()

        def blocking_load(self):
            """Blocking dump meta and data."""
            assert self._data.io and self._meta.io
            self._data.blocking_load()
            self._meta.blocking_load()

        def blocking_dump(self):
            """Blocking dump meta and data."""
            assert self._data.io and self._meta.io
            self._data.blocking_dump()
            self._meta.blocking_dump()

        @classmethod
        def is_correct_meta_data(
            cls,
            data: Ioable | dict | Path,
            meta: Ioable | dict | Path = None
        ) -> bool:
            """Returns True if meta and data may be meta and data of manageable.

            Args:
                data (:obj:`Union[Ioable, dict, Path]`): data.
                meta (:obj:`Uinon[Ioable, dict, Path]`): meta.

            Returns:
                bool.
            """

            try:
                cls(data=data, meta=meta)
                return True
            except Exception:
                return False

    class FileSystemHelper:
        """Contains methods to work with filesystem."""

        DATA_FILENAME = "data"
        """str: name of data file (without extention)"""
        META_FILENAME = "meta"
        """str: name of meta file (without extention)"""

        @staticmethod
        def data_pathes(path: Path) -> list:
            """Return all potential data pathes.

            Args:
                path (:obj:`Path`): Root path.

            Returns:
                :obj:`list` of :obj:`Path`.
            """
            return list(
                filter(
                    lambda x: ".lock" not in x.suffix,
                    path.rglob(Manageable.FileSystemHelper.DATA_FILENAME + ".*")
                )
            )

        @staticmethod
        def meta_pathes(path: Path) -> list:
            """Return all potential meta pathes.

            Args:
                path (:obj:`Path`): Root path.

            Returns:
                :obj:`list` of :obj:`Path`.
            """
            return list(
                filter(
                    lambda x: ".lock" not in x.suffix,
                    path.rglob(Manageable.FileSystemHelper.META_FILENAME + ".*")
                )
            )

        @staticmethod
        def data_path(path: Path) -> Path:
            """Returns path to data file.

            Args:
                path (:obj:`Path`): Root path.

            Returns:
                :obj:`Path`.
            """
            return Manageable.FileSystemHelper.data_pathes(path)[0]

        @staticmethod
        def meta_path(path: Path) -> Path:
            """Returns path to meta file.

            Args:
                path (:obj:`Path`): Root path.

            Returns:
                :obj:`Path`.
            """
            return Manageable.FileSystemHelper.meta_pathes(path)[0]

        @classmethod
        def register(cls, manageable, path: Path):
            """Registeres manageable by path.

            Args:
                manageable (:obj:`Manageable`): Manageable to register.
                path (:obj:`Path`): Path to use.
            """
            assert isinstance(manageable, Manageable)
            assert isinstance(path, Path)
            assert not path.exists()

            path.mkdir()
            manageable._metadata.path = path

            data_path = path.joinpath(
                Path(Manageable.FileSystemHelper.DATA_FILENAME).with_suffix(
                    manageable.state.prefered_suffix
                )
            )
            meta_path = path.joinpath(
                Path(Manageable.FileSystemHelper.META_FILENAME).with_suffix(
                    manageable.state.prefered_suffix
                )
            )

            manageable._metadata.set_path(data_path, meta_path)
            manageable._metadata.dump()

        @classmethod
        def destruct(cls, manageable):
            """Destructs manageable.

            Args:
                manageable (:obj:`Manageable`): Manageable to destruct.

            Note:
                Manageable should be inactive.
            """
            assert isinstance(manageable, Manageable)
            assert not manageable.is_active
            shutil.rmtree(manageable.state.path)

        @classmethod
        def is_correct_tree(cls, clz, path: Path):
            """Returns True if path is possible Manageable file tree.

            Args:
                clz (:obj:`class`): Outer class.
                path (:obj:`Path`): Path to tree.

            Returns:
                bool.
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
                    clz.MetaDataHelper.is_correct_meta_data(
                        data=data_path,
                        meta=meta_path
                    ),
                ])
            except Exception:
                return False

        @classmethod
        def from_tree(cls, clz, path: Path) -> dict:
            """Returns keyword arguments to create :obj:`Manageable` object.

            Args:
                clz (:obj:`Manageable`): Outer class.
                path (:obj:`Path`): Path to tree.

            Returns:
                :obj:`dict` kwargs
            """
            assert isinstance(path, Path)
            assert cls.is_correct_tree(clz, path)

            return {
                "data": clz.FileSystemHelper.data_path(path),
                "meta": clz.FileSystemHelper.meta_path(path),
            }

    class AbstractLoadHelper:
        """Abstract load helper"""

        @staticmethod
        def load_manageable_class(name: str):
            """Loads manageable class by name.

            Args:
                name (str): classname.

            Returns:
                :obj:`class`.
            """
            assert isinstance(name, str)

            for path in Path(__file__).parent.iterdir():
                if path.is_file() and path.stem not in ["manageable", ]:
                    module_name = f"__manageable_realisation_{path.stem}"
                    module = load_module(module_name, path)

                    classes = inspect.getmembers(module)
                    classes = list(filter(lambda x: x[0] == name, classes))

                    if len(classes) >= 1:
                        assert len(classes) == 1
                        return classes[0][1]

            raise NotImplementedError()

        @staticmethod
        def from_tree_unknown(path: Path):
            """Loads registered manageable from tree.
            
            Args:
                path (:obj:`Path`): Path to tree.

            Returns:
                :obj:`Manageable`.
            """
            assert isinstance(path, Path)
            assert Manageable.is_correct_tree(path)

            data_path = Manageable.FileSystemHelper.data_path(path)
            meta_path = Manageable.FileSystemHelper.meta_path(path)

            metadata = Manageable.MetaDataHelper(
                data=Manageable.FileSystemHelper.data_path(path),
                meta=Manageable.FileSystemHelper.meta_path(path)
            )

            return Manageable.AbstractLoadHelper.load_manageable_class(metadata.type)(
                data=data_path, meta=meta_path
            )

        @staticmethod
        def from_descriptor(path: Path):
            """Loads detected manageable from descriptor.

            Args:
                path (:obj:`Path`): Path to tree.

            Returns:
                :obj:`Manageable`.
            """
            assert isinstance(path, Path)

            metadata = Manageable.MetaDataHelper(
                data=path
            )

            return Manageable.AbstractLoadHelper.load_manageable_class(metadata.type)(
                data=path
            )


    @abstractmethod
    def __init__(self,
        data: dict | Ioable | Path | None = None,
        meta: dict | Ioable | Path | None = None
    ):
        """Constructor.

        Args:
            data (:obj:`Union[dict, Ioable, Path, None]`): Data
            meta (:obj:`Union[dict, Ioable, Path, None]`): Meta
            _metadata (:obj:`Union[Manageable.MetaDataHelper, None]`): Metadata
        """

    @abstractmethod
    def start(self):
        """Starts this manageable."""
        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        """Stops this manageable"""
        raise NotImplementedError()

    @property
    def state(self) -> ManageableState:
        """:obj:`ManageableState` state of this manageable"""
        self._metadata.is_active = self.is_active
        return self._metadata.state

    @property
    @abstractmethod
    def is_active(self):
        """bool. True if this manageable is active."""
        raise NotImplementedError()

    def destruct(self):
        """Free all resources (filesystem too)."""
        type(self).FileSystemHelper.destruct(self)

    def register(self, path: Path):
        """Creates filetree by path.

        Args:
            path (:obj:`Path`): Path where manageable should be registered.
        """
        assert isinstance(path, Path)
        type(self).FileSystemHelper.register(self, path)

    def is_registered(self) -> bool:
        """Returns True if this manageable is registered.

        Returns:
            bool.
        """
        return not self._metadata.path is None

    @classmethod
    def is_correct_meta_data(
        cls,
        data: Ioable | dict | Path,
        meta: Ioable | dict | Path = None
    ) -> bool:
        """Returns True if meta and data may be meta and data of manageable.

        Args:
            data (:obj:`Union[Ioable, dict, Path]`): data.
            meta (:obj:`Uinon[Ioable, dict, Path]`): meta.

        Returns:
            bool.
        """
        return cls.MetaDataHelper.is_correct_meta_data(data=data, meta=meta)

    @classmethod
    def is_correct_tree(cls, path: Path) -> bool:
        """Returns True if this manageable is registered.

        Args:
            path (:obj:`Path`): Path to tree.

        Returns:
            bool.
        """
        assert isinstance(path, Path)
        return cls.FileSystemHelper.is_correct_tree(cls, path)

    @classmethod
    def from_tree(cls, path: Path):
        """Loads registered manageable from tree.

        Args:
            path (:obj:`Path`): Path to tree.

        Note:
            Tree should be correct for class.

        Returns:
            :obj:`Manageable`.
        """
        assert isinstance(path, Path)
        assert cls.is_correct_tree(path)
        return cls(**cls.FileSystemHelper.from_tree(cls, path))

    @staticmethod
    def from_tree_unknown(path: Path):
        """Loads registered manageable from tree.
        
        Args:
            path (:obj:`Path`): Path to tree.

        Returns:
            :obj:`Manageable`.
        """
        assert isinstance(path, Path)
        return Manageable.AbstractLoadHelper.from_tree_unknown(path)

    @staticmethod
    def from_descriptor(path: Path):
        """Loads detected manageable from descriptor.

        Args:
            path (:obj:`Path`): Path to tree.

        Returns:
            :obj:`Manageable`.
        """
        assert isinstance(path, Path)
        return Manageable.AbstractLoadHelper.from_descriptor(path)
