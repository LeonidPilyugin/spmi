"""Provides :class:`Pool`.
"""

from pathlib import Path
from spmi.utils.pattern import PatternMatcher
from spmi.utils.logger import Logger
from spmi.core.manageable import Manageable

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
            """
            assert isinstance(path, Path)
            assert path.exists() and path.is_dir()

            self._path = path

        def get_registered_manageables(self):
            """Returns list of registered manageables.

            Returns:
                :obj:`list` of :obj:`spmi.core.manageable.Manageable`.
            """
            result = []

            for path in self._path.iterdir():
                result.append(Manageable.from_directory_unknown(path))

            return result

        def register(self, manageable):
            """Registers a manageable.

            Args:
                manageable (:obj:`spmi.core.manageable.Manageable`): manageable to register.
            """
            assert isinstance(manageable, Manageable)

            path = self._path.joinpath(manageable.state.id)
            assert not path.exists()

            manageable.register(path)


    def __init__(self, path, pm, dm=None):
        """
        Arguments:
            path (:obj:`pathlib.Path`): Path of pool root.
            pm (:obj:`spmi.utils.pattern.PatternMatcher`): Pattern matcher.
            dm (:obj:`list` of :obj:`spmi.core.manageable.Manageable`): List of detected manageables.
        """
        assert isinstance(pm, PatternMatcher)
        assert isinstance(dm, list) or dm is None

        self._logger = Logger("Pool")
        self._logger.debug("Creating Pool object")

        self._pm = pm
        self._fsh = Pool.FileSystemHelper(path)
        self._registered = self._fsh.get_registered_manageables()
        self._detected = dm if dm else []

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

        result = list(filter(lambda x: self._pm.match(pattern, x.state.id),
                           (self._detected if detected else []) +
                           (self._registered if registered else [])))

        self._logger.debug(f"Found {len(result)} results")

        return result

    def register(self, manageable):
        """Registers a detected manageable.

        Args:
            manageable (:obj:`spmi.core.manageable.Manageable`): detected manageable to register.
        """
        self._logger.debug(f"Registering a new manageable \"{manageable.state.id}\"")
        assert isinstance(manageable, Manageable)
        assert manageable in self._detected
        assert manageable.state.id not in map(lambda x: x.state.id, self._registered)

        self._fsh.register(manageable)
        self._registered.append(manageable)

        self._logger.debug(f"Manageable \"{manageable.state.id}\" registered")

    def start(self, pattern):
        """Starts detected manageables by pattern.
        
        Args:
            pattern (:obj:`str`): pattern.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Starting by pattern \"{pattern}\"")

        to_start = self.find(pattern, registered=False)

        for m in to_start:
            self.register(m)

        for m in to_start:
            m.start()

        self._logger.info(f"Started {len(to_start)} manageable{'s' if len(to_start) != 1 else ''}")


    def restart(self, pattern):
        """Restarts registered manageables by pattern.

        Args:
            pattern (:obj:`str`): pattern.

        Note:
            All tasks should be not active.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Restarting manageables by pattern: \"{pattern}\"")

        to_restart = self.find(pattern, detected=False)

        for m in to_restart:
            m.clean()

        for m in to_restart:
            m.start()

        self._logger.info(f"Restarted {len(to_remove)} manageable{'s' if len(to_remove) != 1 else ''}")

    def term(self, pattern):
        """Terminates registered manageables by pattern.

        Args:
            pattern (:obj:`str`): pattern.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Terminated manageables by pattern: \"{pattern}\"")

        to_term = self.find(pattern, detected=False)

        for m in to_term:
            m.term()

        self._logger.info(f"Terminated {len(to_term)} manageable{'s' if len(to_term) != 1 else ''}")

    def kill(self, pattern):
        """Kills registered manageables by pattern.

        Args:
            pattern (:obj:`str`): pattern.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Killing manageables by pattern: \"{pattern}\"")

        to_kill = self.find(pattern, detected=False)

        for m in to_kill:
            m.kill()

        self._logger.info(f"Killed {len(to_kill)} manageable{'s' if len(to_kill) != 1 else ''}")

    def destruct(self, pattern):
        """Destructs manageables by pattern.

        Arguments:
            pattern (:obj:`str`): pattern.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Destructing manageables by pattern: \"{pattern}\"")

        to_remove = self.find(pattern, detected=False)

        for rem in to_remove:
            rem.destruct()
            self._registered.remove(rem)

        self._logger.info(f"Destructed {len(to_remove)} manageable{'s' if len(to_remove) != 1 else ''}")

    def get_status_string(self, pattern):
        """Returns a string containing all manageables corresponding to pattern status data.
        
        Args:
            pattern (:obj:`str`): pattern string.

        Returns:
            :obj:`str`.
        """
        assert isinstance(pattern, str)
        assert self._pm.is_pattern(pattern)

        self._logger.debug(f"Creating status string of registered manageables by pattern \"{pattern}\"")

        to_show = self.find(pattern, detected=False)

        result = ""
        for m in to_show:
            result += str(m.state) + "\n"

        self._logger.info(f"Found {len(to_show)} manageable{'s' if len(to_show) != 1 else ''}")

        return result

    def get_list_string(self):
        """Returns a string containing all manageables brief data.

        Returns:
            :obj:`str`. 
        """
        self._logger.debug("Creating list string of manageables")

        result = ""
        for d in self._detected:
            result += "detected: " + d.state.id + " by path \"" + str(d.state.data_path) + "\"\n"
        for r in self._registered:
            result += "registered: " + r.state.id + "\n"

        self._logger.info(f"{len(self._detected)} manageable{'s' if len(self._detected) != 1 else ''} detected and {len(self._registered)} registered")

        return result

    def finish(self):
        """Finishes all registered manageables."""
        for m in self._registered:
            m.finish()
