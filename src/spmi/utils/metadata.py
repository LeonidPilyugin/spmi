"""Provides :class:`Metadata` and :class:`SubDict`.
"""

from copy import deepcopy
from pathlib import Path
from spmi.utils.io.io import Io
from spmi.utils.logger import Logger

def dontcheck(prop):
    """Decorate properties you don't want to check.

    Some properties of :obj:`MetaData` may be incorrect
    to check on creation (e.g. :py:attr:`MetaData.state`
    creates a :obj:`MetaData` which will call this property
    again if it is not wrapped by this decorator). Wrap
    these properties with ``@dontcheck`` to prevent their
    check on :obj:`MetaData` creation.

    Note:
        :func:`dontcheck` sets ``_spmi_metadata_dontcheck`` attribute of
        ``fget`` function.

    Example:
        A get-only property:

        .. code-block:: Python

            @dontcheck
            @property
            def example_property1(self):
                return self.state

        A get and set property:

        .. code-block:: Python

            @dontcheck
            @property
            def example_property2(self):
                return self.state

            @example_property2.setter
            def example_property2(self, value):
                pass
    """
    assert isinstance(prop, property)
    assert prop.fget

    setattr(prop.fget, "_spmi_metadata_dontcheck", True)

    return prop

class MetaDataNode:
    """Provides property access to ``meta`` and ``data`` dictionaries.

    ``data`` is immutable dictionary, ``meta`` is mutable.
    If ``mutable`` flag is set to ``False``, ``meta`` become immutable.
    """
    def __init__(self, meta=None, data=None, metadata=None, mutable=True, copy=False):
        """
        Args:
            meta (:obj:`Union[dict, None]`): Meta dictionary. Empty if ``None``.
            data (:obj:`Union[dict, None]`): Data dictionary. Empty if ``None``.
            metadata (:obj:`Union[dict, MetaDataNode]`): :class:`MetaDataNode` object.
            mutable (:obj:`bool`): Mutable flag.
            copy (:obj:`bool`): Copy flag. If ``True``, deepcopies ``meta``, ``data`` and ``metadata``.

        Note:
            You can set meta and data or metadata flags at once
        """
        self._logger = Logger(self.__class__.__name__)
        self.__mutable = mutable

        if metadata is None:
            if data is None: data = {}
            if meta is None: meta = {}

            self._meta = meta if not copy else deepcopy(meta)
            self._data = data if not copy else deepcopy(data)

            assert self.check_properties()
        else:
            assert meta is None and data is None
            self._meta = metadata._meta if not copy else deepcopy(metadata._meta)
            self._data = metadata._data if not copy else deepcopy(metadata._data)

    def check_properties(self):
        """Returns ``True`` if all properties of object are correct.

        Iterates throw all properties and tries to get them or
        set with default value if. Skips properties which are
        wrapped with :func:`dontcheck`.

        Returns:
            :obj:`bool`.
        """

        # Check that meta and data is correct:
        # try get every property or set it with
        # default value. If can, continue.
        # If not, wil raise an exception.

        failed_attr = None

        try:
            self._logger.debug("Checking attributes")

            for p in dir(self.__class__):
                failes_attr = p
                property_object = getattr(self.__class__, p)
                if isinstance(
                    property_object,
                    property
                ) and property_object.fget and not hasattr(
                    property_object.fget,
                    "_spmi_metadata_dontcheck"
                ):
                    if self.mutable and property_object.fset:
                        # Set property with default value.
                        setattr(self, p, getattr(self, p))
                    else:
                        # Try to get property.
                        getattr(self, p)
            self._logger.debug("All attributes are correct")
            return True
        except Exception:
            self._logger.debug(f"Failed \"{failed_attr}\" attribute")
            raise # TODO: Remove
            return False

    @property
    def mutable(self) -> bool:
        """:obj:`bool`: True if this object is mutable."""
        return self.__mutable

    @property
    def meta(self) -> dict:
        """:obj:`dict`. Meta dictionary.

        Note:
            If immutable, returns deepcopy.
        """
        assert isinstance(self._meta, dict)
        return self._meta if self.mutable else deepcopy(self._meta)

    @property
    def data(self) -> dict:
        """:obj:`dict`. Data dictionary.

        Note:
            Returns deepcopy.
        """
        assert isinstance(self._data, dict)
        return deepcopy(self._data)


class MetaData(MetaDataNode):
    """Provides property and file access to meta and data.
    """
    def __init__(self, data=None, meta=None, mutable=True, metadata=None, copy=True):
        """
        Args:
            meta (:obj:`Union[dict, pathlib.Path, None]`):
                Meta dictionary. Empty :obj:`dict` if ``None``.
            data (:obj:`Union[dict, pathlib.Path, None]`):
                Data dictionary. Empty :obj:`dict` if ``None``.
            metadata (:obj:`Union[dict, MetaData]`): :class:`MetaData` object.
            mutable (:obj:`bool`): Mutable flag.
            copy (:obj:`bool`): Copy flag. If ``True``, deepcopies ``meta``, ``data`` and ``metadata``.

        Note:
            You can set meta and data or metadata flags at once
        """
        if metadata is None:
            self.__data_io = None
            self.__meta_io = None
            if isinstance(data, Path):
                self.__data_io = Io.get_io(data)
                data = self.__data_io.blocking_load()
            if isinstance(meta, Path):
                self.__meta_io = Io.get_io(meta)
                meta = self.__meta_io.blocking_load()
        else:
            self.__data_io = metadata.__data_io if not (metadata.__data_io and copy) else metadata.__data_io.copy()
            self.__meta_io = metadata.__meta_io if not (metadata.__meta_io and copy) else metadata.__meta_io.copy()

        super().__init__(meta=meta, data=data, metadata=metadata, mutable=mutable, copy=copy)

    @dontcheck
    @property
    def meta_path(self):
        """:obj:`Union[pathlib.Path, None]`. Path to meta file. ``None`` if not exist."""
        return None if not self.__meta_io else self.__meta_io.path.resolve()

    @meta_path.setter
    def meta_path(self, value):
        assert self.mutable
        assert value is None or isinstance(value, Path)

        self.__meta_io = None if value is None else Io.get_io(value)

    @dontcheck
    @property
    def data_path(self):
        """:obj:`Union[pathlib.Path, None]`. Path to data file. ``None`` if not exist."""
        return None if not self.__data_io else self.__data_io.path.resolve()

    @data_path.setter
    def data_path(self, value):
        assert self.mutable
        assert value is None or isinstance(value, Path)

        self.__data_io = None if value is None else Io.get_io(value)

    @dontcheck
    @property
    def state(self):
        """:obj:`MetaData` Copies self to immutable object of ``self.__class__``."""
        return self.__class__(metadata=self, mutable=False)

    def load(self):
        """Loads meta and data from files.

        Note:
            Should be mutable.
        """
        self._logger.debug("Loading")
        assert self.mutable
        assert self.__data_io and self.__meta_io
        self._data = self.__data_io.load()
        self._meta = self.__meta_io.load()

    def dump(self):
        """Dumps meta and data.

        Note:
            Should be mutable.
        """
        self._logger.debug("Dumping")
        assert self.mutable
        assert self.__data_io and self.__meta_io
        self.__data_io.dump(self._data)
        self.__meta_io.dump(self._meta)

    def lock(self):
        """Locks meta and data files.

        Note:
            Should be mutable.
        """
        self._logger.debug("Locking")
        assert self.mutable
        assert self.__data_io and self.__meta_io
        self.__data_io.lock()
        self.__meta_io.lock()

    def acquire(self):
        """Acquires meta and data files.

        Note:
            Should be mutable.
        """
        self._logger.debug("Acquiring")
        assert self.mutable
        assert self.__data_io and self.__meta_io
        self.__data_io.acquire()
        self.__meta_io.acquire()

    def blocking_load(self):
        """Blocks and loads meta and data from files.

        Note:
            Should be mutable.
        """
        self._logger.debug("Procesing blocking load.")
        assert self.mutable
        assert self.__data_io and self.__meta_io
        self._data = self.__data_io.blocking_load()
        self._meta = self.__meta_io.blocking_load()

    def blocking_dump(self):
        """Blocks and dumps meta and data.

        Note:
            Should be mutable.
        """
        self._logger.debug("Processing blocking dump.")
        assert self.mutable
        assert self.__data_io and self.__meta_io
        self.__data_io.blocking_dump(self._data)
        self.__meta_io.blocking_dump(self._meta)

    @classmethod
    def is_correct_meta_data(cls, data, meta = None):
        """Returns ``True`` if meta and data may be meta and data of manageable.

        Args:
            data (:obj:`Union[dict, Pathlib.path]`): Data.
            meta (:obj:`Uinon[dict, Pathlib.path]`): Meta.

        Returns:
            :obj:`bool`.
        """

        assert isinstance(data, (dict, Path)) or data is None
        assert isinstance(meta, (dict, Path)) or meta is None

        try:
            cls(data=data, meta=meta)
            return True
        except Exception:
            return False

