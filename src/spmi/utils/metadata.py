"""
.. module:: metadata.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

from copy import deepcopy
from pathlib import Path
from spmi.utils.io.io import Io
from spmi.utils.io.ioable import Ioable

def _check_properties(self):
    # Check that meta and data is correct:
    # try get every property or set it with
    # default value. If can, continue.
    # If not, wil raise an exception.
    try:
        for p in dir(self.__class__):
            property_object = getattr(self.__class__, p)
            if isinstance(
                property_object,
                property
            ) and property_object.fget and not hasattr(
                property_object.fget,
                "_spmi_metadatahelper_dontcheck"
            ):
                if self.mutable and property_object.fset:
                    # Set property with default value.
                    setattr(self, p, getattr(self, p))
                else:
                    # Try to get property.
                    getattr(self, p)
        return True
    except Exception:
        raise
        return False


def dontcheck(prop):
    """Don't check decorator.

    Decorate properties you want to not check with it.
    """
    setattr(prop.fget, "_spmi_metadatahelper_dontcheck", True)
    return prop

class MetaData:
    """Provides access to meta and data."""
    def __init__(
        self,
        data: Ioable | dict | Path | None,
        meta: Ioable | dict | Path | None = None,
        mutable: bool = True,
        metadata = None,
        copy: bool = True,
    ):
        """Constructor.

        Args:
            data (:obj:`Union[Ioable, dict]`): data.
            meta (:obj:`Union[Ioable, dict]`): meta.
            prefered_suffix (str): preferred suffix.
        """
        assert metadata is None != (data is None or meta is None)
        
        def load(value) -> Ioable:
            assert isinstance(value, (Ioable, dict, Path)) or value is None
            if isinstance(value, Ioable):
                return value if not copy else value.copy()
            if isinstance(value, Path):
                io = Ioable(io=Io.get_io(value))
                io.blocking_load()
                return io
            if isinstance(value, dict):
                return Ioable(data=(value if not copy else deepcopy(value)))
            return Ioable(data=None)

        self.__data = load(data if not metadata else metadata.__data)
        self.__meta = load(meta if not metadata else metadata.__meta)
        assert isinstance(self.__meta, Ioable)
        assert isinstance(self.__data, Ioable)

        self._mutable = mutable
        assert _check_properties(self)

    @property
    def mutable(self) -> bool:
        """bool. True if this object is mutable."""
        return self._mutable

    @property
    def _meta(self) -> dict:
        """:obj:`dict`. Meta dictionary."""
        assert isinstance(self.__meta.data, dict)
        return self.__meta.data if self.mutable else deepcopy(self.__meta.data)

    @property
    def _data(self) -> dict:
        """:obj:`dict`. Data dictionary."""
        assert isinstance(self.__meta.data, dict)
        return self.__data.data if self.mutable else deepcopy(self.__data.data)

    @dontcheck
    @property
    def meta_path(self) -> Path | None:
        """:obj:`Union[Path, None]`. Path to meta file."""
        return None if not self.__meta.io else self.__meta.io.path.resolve()

    @meta_path.setter
    def meta_path(self, value: str | Path | None):
        assert self.mutable
        assert value is None or isinstance(value, (str, Path))

        if not value is None:
            if not isinstance(value, Path):
                value = Path(value)
            self.__meta.io = Io.get_io(value)
        else:
            self.__meta.io = None

    @dontcheck
    @property
    def data_path(self) -> Path | None:
        """:obj:`Union[Path, None]`. Path to data file."""
        return None if not self.__data.io else self.__data.io.path.resolve()

    @data_path.setter
    def data_path(self, value: Path | str | None):
        assert self.mutable
        assert value is None or isinstance(value, (str, Path))

        if not value is None:
            if not isinstance(value, Path):
                value = Path(value)
            self.__data.io = Io.get_io(value)
        else:
            self.__data.io = None

    @dontcheck
    @property
    def state(self):
        """:obj:`ManageableState` Copy to immutable state."""
        return self.__class__(data=self.__data, meta=self.__meta, mutable=False)

    def load(self):
        """Load meta and data."""
        assert self.mutable
        assert self.__data.io and self.__meta.io
        self.__data.load()
        self.__meta.load()

    def dump(self):
        """Dump meta and data."""
        assert self.mutable
        assert self.__data.io and self.__meta.io
        self.__data.dump()
        self.__meta.dump()

    def lock(self):
        """Lock meta and data."""
        assert self.mutable
        assert self.__data.io and self.__meta.io
        self.__data.lock()
        self.__meta.lock()

    def acquire(self):
        """Acquire meta and data."""
        assert self.mutable
        assert self.__data.io and self.__meta.io
        self.__data.acquire()
        self.__meta.acquire()

    def blocking_load(self):
        """Blocking dump meta and data."""
        assert self.mutable
        assert self.__data.io and self.__meta.io
        self.__data.blocking_load()
        self.__meta.blocking_load()

    def blocking_dump(self):
        """Blocking dump meta and data."""
        assert self.mutable
        assert self.__data.io and self.__meta.io
        self.__data.blocking_dump()
        self.__meta.blocking_dump()

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

class SubDict:
    """Provides access to metadata without io"""
    def __init__(self, meta: dict, data: dict, mutable: bool = True, copy: bool = False):
        self.__meta = meta if not copy else deepcopy(meta)
        self.__data = data if not copy else deepcopy(data)
        self._mutable = mutable
        assert _check_properties(self)

    @property
    def mutable(self) -> bool:
        """bool. True if this object is mutable."""
        return self._mutable

    @property
    def _meta(self) -> dict:
        """:obj:`dict`. Meta dictionary."""
        assert isinstance(self.__meta, dict)
        return self.__meta if self.mutable else deepcopy(self.__meta)

    @property
    def _data(self) -> dict:
        """:obj:`dict`. Data dictionary."""
        assert isinstance(self.__data, dict)
        return self.__data if self.mutable else deepcopy(self.__data)

