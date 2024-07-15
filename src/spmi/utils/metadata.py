"""Provides :class:`Metadata` and :class:`SubDict`.
"""

from copy import deepcopy
from pathlib import Path
from spmi.utils.io.io import Io
from spmi.utils.logger import Logger
from spmi.utils.exception import SpmiException


class MetaDataError(SpmiException):
    pass


class IncorrectProperty(MetaDataError):
    pass


def dontcheck(prop):
    """Decorate properties you don't want to check.

    Some properties of :obj:`MetaData` may be incorrect
    to check on creation (e.g. :py:attr:`MetaData.state`
    creates a :obj:`MetaData` which will call this property
    again if it is not wrapped by this decorator). Wrap
    these properties with ``@dontcheck`` to prevent their
    check on :obj:`MetaData` creation.

    Rasies:
        :class:`TypeError`
        :class:`AttributeError`

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
    if not isinstance(prop, property):
        raise TypeError(f"Must decorate a property, not {type(prop)}")
    if not prop.fget:
        raise AttributeError("Property object must have a getter method")

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

        Raises:
            :class:`TypeError`
            :class:`ValueError`
            :class:`IncorrectProperty`
        """
        self._logger = Logger(self.__class__.__name__)
        self.__mutable = mutable

        if metadata is None:
            if data is None:
                data = {}
            if meta is None:
                meta = {}

            if not isinstance(meta, dict):
                raise TypeError(f"meta must be a dict, not {type(meta)}")
            if not isinstance(data, dict):
                raise TypeError(f"data must be a dict, not {type(data)}")
            try:
                self._meta = meta if not copy else deepcopy(meta)
            except Exception as e:
                raise ValueError(f"meta must be a dict which can be deepcopied")
            try:
                self._data = data if not copy else deepcopy(data)
            except Exception as e:
                raise ValueError(f"data must be a dict which can be deepcopied")
        else:
            if not (meta is None and data is None):
                raise ValueError(
                    f"metadata is not None, so meta and data must be None, not {meta} and {data}"
                )
            if not isinstance(metadata, MetaDataNode):
                raise TypeError(
                    f"metadata must be a MetaDataNode, not {type(metadata)}"
                )
            self._meta = metadata._meta if not copy else deepcopy(metadata._meta)
            self._data = metadata._data if not copy else deepcopy(metadata._data)
        self.check_properties()

    def check_properties(self):
        """Raises :class:`IncorrectProperty` exception if properties are incorrect..

        Iterates throw all properties and tries to get them or
        set with default value if. Skips properties which are
        wrapped with :func:`dontcheck`.

        Raises:
            :class:`IncorrectProperty`
        """

        # Check that meta and data is correct:
        # try get every property or set it with
        # default value. If can, continue.
        # If not, wil raise an exception.

        try:
            self._logger.debug("Checking attributes")

            for p in dir(self.__class__):
                property_object = getattr(self.__class__, p)
                if (
                    isinstance(property_object, property)
                    and property_object.fget
                    and not hasattr(property_object.fget, "_spmi_metadata_dontcheck")
                ):
                    if self.mutable and property_object.fset:
                        # Set property with default value.
                        setattr(self, p, getattr(self, p))
                    else:
                        # Try to get property.
                        getattr(self, p)
            self._logger.debug("All attributes are correct")
        except Exception as e:
            self._logger.debug(f'Failed "{p}" attribute')
            raise IncorrectProperty(f'Property "{p}" is incorrect:\n{e}') from e

    @property
    def mutable(self):
        """:obj:`bool`: True if this object is mutable."""
        return self.__mutable

    @property
    def meta(self):
        """:obj:`dict`. Meta dictionary.

        Note:
            If immutable, returns deepcopy.
        """
        assert isinstance(self._meta, dict)
        return self._meta if self.mutable else deepcopy(self._meta)

    @property
    def data(self):
        """:obj:`dict`. Data dictionary.

        Note:
            Returns deepcopy.
        """
        assert isinstance(self._data, dict)
        return deepcopy(self._data)


class MetaData(MetaDataNode):
    """Provides property and file access to meta and data."""

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

        Raises:
            :class:`TypeError`
            :class:`ValueError`
            :class:`IoException`
            :class:`MetaDataError`
        """
        self.__entered = False
        if metadata is None:
            self.__data_io = None
            self.__meta_io = None
            if isinstance(data, Path):
                self.__data_io = Io.get_io(data)
                data = self.__data_io.blocking_load()
            if isinstance(meta, Path):
                self.__meta_io = Io.get_io(meta)
                meta = self.__data_io.blocking_load()
        else:
            self.__data_io = (
                metadata.__data_io
                if not (metadata.__data_io and copy)
                else metadata.__data_io.copy()
            )
            self.__meta_io = (
                metadata.__meta_io
                if not (metadata.__meta_io and copy)
                else metadata.__meta_io.copy()
            )

        try:
            super().__init__(
                meta=meta, data=data, metadata=metadata, mutable=mutable, copy=copy
            )
        except IncorrectProperty as e:
            msg = f'Cannot load from "{data}"'
            if meta:
                msg += f' and "{meta}"'
            msg += f":\n{e}"
            raise MetaDataError(msg) from e

    @dontcheck
    @property
    def meta_path(self):
        """:obj:`Union[pathlib.Path, None]`. Path to meta file. ``None`` if not exist.

        Raises:
            :class:`MetaDataError`
            :class:`TypeError`
        """
        return None if not self.__meta_io else self.__meta_io.path

    @meta_path.setter
    def meta_path(self, value):
        if self.__entered:
            raise MetaDataError('Cannot change meta path, entered a "with" statement')
        if not self.mutable:
            raise MetaDataError("Must be mutable")
        if not (value is None or isinstance(value, Path)):
            raise TypeError(f"value must be a None or pathlib.Path, not {type(value)}")

        self.__meta_io = None if value is None else Io.get_io(value)

    @meta_path.deleter
    def meta_path(self):
        if not self.mutable:
            raise MetaDataError("Must be mutable")
        if self.__entered:
            self.__meta_io.__exit__(None, None, None)
        self.__meta_io = None

    @dontcheck
    @property
    def data_path(self):
        """:obj:`Union[pathlib.Path, None]`. Path to data file. ``None`` if not exist.

        Raises:
            :class:`MetaDataError`
            :class:`TypeError`
        """
        return None if not self.__data_io else self.__data_io.path

    @data_path.setter
    def data_path(self, value):
        if self.__entered:
            raise MetaDataError('Cannot change data path, entered a "with" statement')
        if not self.mutable:
            raise MetaDataError("Must be mutable")
        if not (value is None or isinstance(value, Path)):
            raise TypeError(f"value must be a None or pathlib.Path, not {type(value)}")

        self.__data_io = None if value is None else Io.get_io(value)

    @data_path.deleter
    def data_path(self):
        if not self.mutable:
            raise MetaDataError("Must be mutable")
        if self.__entered:
            self.__data_io.__exit__(None, None, None)
        self.__data_io = None

    @dontcheck
    @property
    def state(self):
        """:obj:`MetaData` Copies self to immutable object of ``self.__class__``."""
        return self.__class__(metadata=self, mutable=False)

    def load(self):
        """Loads meta and data from files.

        Note:
            Should be mutable.

        Raises:
            :class:`MetaDataError`
            :class:`IoException`
        """
        self._logger.debug("Loading")
        if not self.mutable:
            raise MetaDataError("Must be mutable")
        if not self.__data_io:
            raise MetaDataError("Data path must be specified")
        if not self.__meta_io:
            raise MetaDataError("Meta path must be specified")
        self._data = self.__data_io.load()
        self._meta = self.__meta_io.load()

    def dump(self):
        """Dumps meta and data.

        Note:
            Should be mutable.

        Raises:
            :class:`MetaDataError`
            :class:`IoException`
        """
        self._logger.debug("Dumping")
        if not self.mutable:
            raise MetaDataError("Must be mutable")
        if not self.__data_io:
            raise MetaDataError("Data path must be specified")
        if not self.__meta_io:
            raise MetaDataError("Meta path must be specified")
        self.__data_io.dump(self._data)
        self.__meta_io.dump(self._meta)

    def blocking_load(self):
        """Blocks and loads meta and data from files.

        Note:
            Should be mutable.

        Raises:
            :class:`MetaDataError`
            :class:`IoException`
        """
        self._logger.debug("Procesing blocking load.")
        if self.__entered:
            raise MetaDataError('Cannot process blocking load inside "with" statement')
        if not self.mutable:
            raise MetaDataError("Must be mutable")
        if not self.__data_io:
            raise MetaDataError("Data path must be specified")
        if not self.__meta_io:
            raise MetaDataError("Meta path must be specified")
        self._data = self.__data_io.blocking_load()
        self._meta = self.__meta_io.blocking_load()

    def blocking_dump(self):
        """Blocks and dumps meta and data.

        Note:
            Should be mutable.

        Raises:
            :class:`MetaDataError`
            :class:`IoException`
        """
        self._logger.debug("Processing blocking dump.")
        if self.__entered:
            raise MetaDataError('Cannot process blocking dump inside "with" statement')
        if not self.mutable:
            raise MetaDataError("Must be mutable")
        if not self.__data_io:
            raise MetaDataError("Data path must be specified")
        if not self.__meta_io:
            raise MetaDataError("Meta path must be specified")
        self.__data_io.blocking_dump(self._data)
        self.__meta_io.blocking_dump(self._meta)

    def __enter__(self):
        self._logger.debug('Entering "with" statement')
        if self.__entered:
            raise MetaDataError('Already entered "with" statement')
        self.__meta_io.__enter__()
        self.__data_io.__enter__()
        self.__entered = True
        self.load()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._logger.debug('Exiting "with" statement')
        self.__entered = False
        if self.__meta_io and self.__data_io:
            self.dump()
        if self.__meta_io:
            self.__meta_io.__exit__(exc_type, exc_value, traceback)
        if self.__data_io:
            self.__data_io.__exit__(exc_type, exc_value, traceback)

    @classmethod
    def is_correct_meta_data(cls, data, meta=None):
        """Returns ``True`` if meta and data may be meta and data of manageable.

        Args:
            data (:obj:`Union[dict, Pathlib.path]`): Data.
            meta (:obj:`Uinon[dict, Pathlib.path]`): Meta.

        Returns:
            :obj:`bool`.

        Raises:
            :class:`TypeError`
            :class:`IoException`
        """
        try:
            cls(data=data, meta=meta)
            return True
        except IncorrectProperty:
            return False
