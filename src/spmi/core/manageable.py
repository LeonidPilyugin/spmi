"""
.. module:: manageable.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import inspect
import shutil
from abc import abstractmethod, ABCMeta
from pathlib import Path
from spmi.utils.io.ioable import Ioable
from spmi.utils.load import load_module
from spmi.utils.metadata import MetaData

def manageable(cls):
    """Manageable decorator. All manageables should be decoratet with it."""
    def __new_init__(self, *args, data=None, meta=None, **kwargs):
        assert data

        if "_metadata" not in dir(self):
            self._metadata = cls.MetaDataHelper(data=data, meta=meta, **kwargs)
            self._metadata._outer_object = self

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
    """This class describes object which can be managed."""
    class MetaDataHelper(MetaData):
        """Provides access to meta and data."""
        @property
        def prefered_suffix(self) -> str:
            """str. Prefered suffix."""
            if "prefered_suffix" in self._meta:
                return self._meta["prefered_suffix"]
            assert self.data_path
            return self.data_path.suffix

        @prefered_suffix.setter
        def prefered_suffix(self, value: str):
            assert isinstance(value, str)
            assert self.mutable
            self._meta["prefered_suffix"] = value

        @property
        def type(self) -> str:
            """str. Type"""
            keys = list(self._data.keys())
            assert len(keys) == 1
            key = keys[0]
            assert isinstance(key, str)

            return key

        @property
        def m_data(self) -> dict:
            """:obj:`dict`. Manageable data."""
            return self._data[self.type]

        @property
        def id(self) -> str:
            """str. Id."""
            return str(self.m_data["id"])

        @property
        def path(self) -> Path | None:
            """:obj:`Path`. Path"""
            if "path" in self._meta:
                res = self._meta["path"]
                if not res is None:
                    res = Path(res)
                return res
            return None

        @path.setter
        def path(self, value: Path | None):
            assert value is None or isinstance(value, Path)
            assert self.mutable
            self._meta["path"] = value if value is None else str(value)

        def __str__(self):
            return f"{self.type}: {self.id}"

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

            Note:
                Manageable should be inactive.
            """
            assert isinstance(manageable, Manageable)
            assert not manageable.is_active
            shutil.rmtree(manageable.state.path)

        @classmethod
        def is_correct_tree(cls, path: Path):
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
                    cls._outer_class.MetaDataHelper.is_correct_meta_data(
                        data=data_path,
                        meta=meta_path
                    ),
                ])
            except Exception:
                return False

        @classmethod
        def from_tree(cls, path: Path) -> dict:
            """Returns keyword arguments to create :obj:`Manageable` object.

            Args:
                clz (:obj:`Manageable`): Outer class.
                path (:obj:`Path`): Path to tree.

            Returns:
                :obj:`dict` kwargs
            """
            assert isinstance(path, Path)
            assert cls.is_correct_tree(path)

            return {
                "data": cls.data_path(path),
                "meta": cls.meta_path(path),
            }

    class LoadHelper:
        """Abstract load helper"""

        @staticmethod
        def get_class_name(string: str) -> str:
            """Converts string to class name.

            Args:
                string (str): string.

            Returns:
                str.
            """
            return "".join([x.capitalize() for x in string.split()]) + "Manageable"

        @staticmethod
        def load_manageable_class(name: str):
            """Loads manageable class by name.

            Args:
                name (str): classname.

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

            return Manageable.LoadHelper.load_manageable_class(metadata.type)(
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

            return Manageable.LoadHelper.load_manageable_class(metadata.type.capitalize())(
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
    @abstractmethod
    def is_active(self) -> bool:
        """bool. True if manageable is active."""
        raise NotImplementedError()

    @property
    def state(self):
        """:obj:`ManageableState` state of this manageable"""
        return self._metadata.state

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
        return not self._metadata.meta_path is None

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
        return cls.FileSystemHelper.is_correct_tree(path)

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
        return cls(**cls.FileSystemHelper.from_tree(path))

    @staticmethod
    def from_tree_unknown(path: Path):
        """Loads registered manageable from tree.
        
        Args:
            path (:obj:`Path`): Path to tree.

        Returns:
            :obj:`Manageable`.
        """
        assert isinstance(path, Path)
        return Manageable.LoadHelper.from_tree_unknown(path)

    @staticmethod
    def from_descriptor(path: Path):
        """Loads detected manageable from descriptor.

        Args:
            path (:obj:`Path`): Path to tree.

        Returns:
            :obj:`Manageable`.
        """
        assert isinstance(path, Path)
        return Manageable.LoadHelper.from_descriptor(path)
