"""Provides :class:`Pool`.
"""

from pathlib import Path
from spmi.utils.pattern import PatternMatcher
from spmi.utils.logger import Logger
from spmi.core.manageable import Manageable, ManageableException
from spmi.utils.exception import SpmiException
from spmi.utils.metadata import MetaDataError
from spmi.utils.io.io import Io

class PoolException(SpmiException):
    pass

class Pool:
    """A class which helps to manage Manageables."""
    class FileSystemHelper:
        """Provides several methods to work with filesystem."""
        def __init__(self, home, path):
            """
            Arguments:
                path (:obj:`pathlib.Path`): Path where directory of manageables is placed.

            Note:
                ``path`` should exist and be a directory.

            Raises:
                :class:`TypeError`
                :class:`PoolException`
            """
            self._logger = Logger(self.__class__.__name__)
            self._logger.debug(f"Creating object with path {path} and home {home}")

            if not isinstance(path, list):
                raise TypeError(f"path must be a list, not {type(dm)}")
            if not isinstance(home, Path):
                raise TypeError(f"home must be a pathlib.Path, not {type(path)}")
            if not home.exists():
                home.mkdir()
            if not home.is_dir():
                raise PoolException(f"Path \"{path}\" exists and is not a directory")

            self._home = home
            self._path = path

        def get_registered_manageables(self):
            """Returns list of registered manageables.

            Returns:
                :obj:`list` of :obj:`spmi.core.manageable.Manageable`.
            """
            self._logger.debug("Loading registered manageables")
            result = []

            for path in self._home.iterdir():
                result.append(Manageable.from_directory_unknown(path))

            return result

        def register(self, manageable):
            """Registers a manageable.

            Args:
                manageable (:obj:`spmi.core.manageable.Manageable`): manageable to register.

            Raises:
                :class:`TypeError`
                :class:`ManageableException`
            """
            if not isinstance(manageable, Manageable):
                raise TypeError(f"manageable must be a Manageable, not {type(manageable)}")

            self._logger.debug("Registering a manageable {manageable.state.id}")

            path = self._home.joinpath(manageable.state.id)
            manageable.register(path)

        def get_detected_manageables(self):
            """Return list of found descriptors.
            
            Returns:
                :obj:`list` of :obj:`spmi.manageable.Manageable`:
                :obj:`list` of detected manageables.
            """
            self._logger.debug("Loading manageables descriptors")

            manageables = []

            for root in self._path:
                for path_object in root.rglob("*"):
                    if path_object.is_file() and Io.has_io(path_object.suffix):
                        new_manageable = Manageable.from_descriptor(path_object)
                        manageables.append(new_manageable)

            return manageables


    def __init__(self, home, path, pm):
        """
        Arguments:
            home (:obj:`pathlib.Path`): Path of pool root.
            path (:obj:`list` of :obj:`Manageable`): List of pathes to search descriptors
            pm (:obj:`spmi.utils.pattern.PatternMatcher`): Pattern matcher.

        Raises:
            :class:`TypeError`
            :class:`PoolException`
            :class:`ManageableException`
            :class:`MetaDataError`
        """
        if not isinstance(pm, PatternMatcher):
            raise TypeError(f"pm must be a PatternMatcher, not {type(pm)}")

        self._logger = Logger("Pool")
        self._logger.debug("Creating Pool object")

        self._pm = pm
        self._fsh = Pool.FileSystemHelper(home, path)
        self._registered = self._fsh.get_registered_manageables()
        self._detected = self._fsh.get_detected_manageables()

    @property
    def detected(self):
        """:obj:`list` of :obj:`Manageable`. Copy of list with detected manageables."""
        return list(self._detected)

    @property
    def registered(self):
        """:obj:`list` of :obj:`Manageable`. Copy of list with registered manageables."""
        return list(self._registered)
        
    def find(self, pattern, detected=True, registered=True):
        """Return list of manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern to find.
            detected (:obj:`bool`): If True, search in detected list.
            registered (:obj:`bool`): If True, search in registered list.

        Note:
            If both ``detected`` and ``registered`` arguments are ``False``,
            will return an empty list.

        Returns:
            :obj:`list` of :obj:`spmi.core.manageable.Manageable`.
        """
        self._logger.debug(f"Searching \"{pattern}\"; detected: {detected}, registered: {registered}")

        result = []
        for m in self._registered if registered else []:
            with m:
                if self._pm.match(pattern, m.state.id):
                    result.append(m)
        for m in self._detected if detected else []:
            if self._pm.match(pattern, m.state.id):
                result.append(m)

        self._logger.debug(f"Found {len(result)} results")

        return result

    def register(self, manageable):
        """Registers a detected manageable.

        Args:
            manageable (:obj:`spmi.core.manageable.Manageable`): detected manageable to register.

        Raises:
            :class:`TypeError`
            :class:`ManageableException`
            :class:`PoolException`
        """
        self._logger.debug(f"Registering a new manageable \"{manageable.state.id}\"")
        if manageable.state.id in map(lambda x: x.state.id, self._registered):
            raise PoolException(f"Manageable with ID \"{manageable.state.id}\" is already registered")
        if not isinstance(manageable, Manageable):
            raise TypeError(f"manageable must be a Manageable, not {type(manageable)}")

        self._fsh.register(manageable)
        self._registered.append(manageable)

        self._logger.debug(f"Manageable \"{manageable.state.id}\" registered")
