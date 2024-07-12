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
        def __init__(self, path):
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
            self._logger.debug(f"Creating object with path {path}")

            if not isinstance(path, Path):
                raise TypeError(f"path must be a pathlib.Path, not {type(dm)}")
            if not path.exists():
                path.mkdir()
            if not path.is_dir():
                raise PoolException(f"Path \"{path}\" exists and is not a directory")

            self._path = path

        def get_registered_manageables(self):
            """Returns list of registered manageables.

            Returns:
                :obj:`list` of :obj:`spmi.core.manageable.Manageable`.
            """
            self._logger.debug("Loading registered manageables")
            result = []

            for path in self._path.iterdir():
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

            path = self._path.joinpath(manageable.state.id)
            manageable.register(path)


    def __init__(self, path, pm):
        """
        Arguments:
            path (:obj:`pathlib.Path`): Path of pool root.

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
        self._fsh = Pool.FileSystemHelper(path)
        self._manageables = self._fsh.get_registered_manageables()

    @property
    def manageables(self):
        """:obj:`list` of :obj:`Manageable`. Copy of list with registered manageables."""
        return list(self._manageables)
        
    def find(self, pattern):
        """Return list of manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern to find.

        Returns:
            :obj:`list` of :obj:`spmi.core.manageable.Manageable`.
        """
        self._logger.debug(f"Searching \"{pattern}\"")

        result = []
        for m in self._manageables:
            with m:
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
        if manageable.state.id in map(lambda x: x.state.id, self._manageables):
            raise PoolException(f"Manageable with ID \"{manageable.state.id}\" is already registered")
        if not isinstance(manageable, Manageable):
            raise TypeError(f"manageable must be a Manageable, not {type(manageable)}")

        self._fsh.register(manageable)
        self._manageables.append(manageable)

        self._logger.debug(f"Manageable \"{manageable.state.id}\" registered")
