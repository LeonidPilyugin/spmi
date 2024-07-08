"""
.. module:: pool.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

from pathlib import Path
from typing import List
from spmi.utils.pattern import PatternMatcher
from spmi.utils.logger import Logger
from spmi.core.manageable import Manageable

class Pool:
    """A class which helps to manage Manageables"""
    class FileSystemHelper:
        """Helper class which provides several methods to work with filesystem"""
        def __init__(self, path: Path):
            """Constructor.

            Arguments:
                path (:obj:`Path`): root path.
            """
            assert isinstance(path, Path)
            assert path.exists() and path.is_dir()

            self._path = path

        def get_registered_manageables(self) -> List[Manageable]:
            """Returns list of registered manageables

            Returns:
                :obj:`list` of :obj:`Manageable`.
            """
            result = []

            for path in self._path.iterdir():
                result.append(Manageable.from_tree_unknown(path))

            return result

        def register(self, manageable: Manageable):
            """Registers a manageable

            Args:
                manageable (:obj:`Manageable`): manageable to register.
            """
            assert isinstance(manageable, Manageable)
            assert not manageable.is_registered()

            path = self._path.joinpath(manageable.state.id)
            assert not path.exists()

            manageable.register(path)


    def __init__(self, path: Path, pm: PatternMatcher, dm: List[Manageable] = None):
        """Constructor.

        Arguments:
            path (:obj:`Path`): Path of pool root.
            pm (:obj:`PatternMatcher`): Pattern matcher.
            dm (:obj:`list` of :obj:`Manageable`): List of detected manageables.
        """
        assert isinstance(pm, PatternMatcher)
        assert isinstance(dm, list) or dm is None

        self._logger = Logger("Pool")
        self._logger.debug("Creating Pool object")

        self._pm = pm
        self._fsh = Pool.FileSystemHelper(path)
        self._registered = self._fsh.get_registered_manageables()
        self._detected = dm if dm else []

    def find(self,
             pattern: str,
             detected: bool = True,
             registered: bool = True) -> List[Manageable]:
        """Return list of manageables corresponding to pattern

        Args:
            pattern (str): Pattern to find
            detected (bool): If True, search in detected list
            registered (bool): If True, search in registered list

        Note:
            If both `detected` and `registered` arguments are False,
            will return an empty list.

        Returns:
            :obj:`list` of :obj:`Manageable`
        """
        return list(filter(lambda x: self._pm.match(pattern, x.state.id),
                           (self._detected if detected else []) +
                           (self._registered if registered else [])))

    def register(self, manageable: Manageable):
        """Registers a detected manageable

        Args:
            manageable (:obj:`Manageable`): detected manageable to register
        """
        self._logger.debug(f"Registering a new manageable \"{manageable.state.id}\"")
        assert isinstance(manageable, Manageable)
        assert manageable in self._detected

        self._fsh.register(manageable)
        self._detected.remove(manageable)
        self._registered.append(manageable)

    def start(self, pattern: str):
        """Starts detected manageables by pattern
        
        Args:
            pattern (str): pattern.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Starting by pattern \"{pattern}\"")

        registered_ids = [m.state.id for m in self._registered]
        for m in self.find(pattern, registered=False):
            self._logger.debug(f"Starting manageable \"{m.state.id}\"")
            assert not m.state.id in registered_ids
            self.register(m)

    def restart(self, pattern: str):
        """Restarts registered manageables by pattern.

        Args:
            pattern (str): pattern.

        Note:
            All tasks should be not active.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Restarting manageables by pattern: \"{pattern}\"")

        for m in self.find(pattern, detected=False):
            assert m.state.can_destruct
            m.clean()
            m.start()

    def stop(self, pattern: str):
        """Stops registered manageables by pattern.

        Args:
            pattern (str): pattern.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Stopping manageables by pattern: \"{pattern}\"")

        for m in self.find(pattern, detected=False):
            m.stop()

    def destruct(self, pattern: str):
        """Destructs manageables by pattern.

        Arguments:
            pattern (str): pattern.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Destructing manageables by pattern: \"{pattern}\"")

        to_remove = self.find(pattern, detected=False)

        for rem in to_remove:
            self._logger.debug(f"Destructing manageable \"{rem.state.id}\"")
            rem.destruct()
            self._registered.remove(rem)

    def get_status_string(self, pattern: str) -> str:
        """Returns a string containing all manageables corresponding to pattern status data
        
        Args:
            pattern (str): pattern string.

        Returns:
            str.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Printing statuses of registered manageables by pattern \"{pattern}\"")

        result = ""
        for m in self.find(pattern, detected=False):
            result += str(m.state) + "\n"

        return result

    def get_list_string(self) -> str:
        """Returns a string containing all manageables brief data

        Returns:
            str.            
        """
        self._logger.debug("Creating list string of manageables")

        result = ""
        for d in self._detected:
            result += "detected: " + d.state.id + " by path \"" + str(d.state.data_path) + "\"\n"
        for r in self._registered:
            result += "registered: " + r.state.id + "\n"

        return result
