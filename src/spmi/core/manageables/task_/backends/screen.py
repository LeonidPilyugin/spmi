"""Provides :class:`ScreenBackend`.
"""

import os
import subprocess
from spmi.core.manageables.task import TaskManageable, BackendException
from spmi.utils.logger import Logger

class ScreenBackendException(BackendException):
    pass

class ScreenBackend(TaskManageable.Backend):
    """GNU Screen backend."""
    def __init__(self):
        self._logger = Logger(self.__class__.__name__)
        self._logger.debug("Creating backend")
        self._screen_ids = set()
        self.load_screens()

    def load_screens(self):
        """Loads all screen sessions."""
        self._logger.debug("Loading IDs of screens")

        # modified code from
        # https://github.com/Christophe31/screenutils
        screen_ids = [
            l.split(".")[0].strip()
            for l in subprocess.getoutput("screen -ls").split('\n')
            if "\t" in l and ".".join(l.split(".")[1:]).split("\t")[0]
        ]

        self._screen_ids = set(screen_ids)

        if len(self._screen_ids) != len(screen_ids):
            raise ScreenBackendException("Found equal IDs in \"screen -ls\"")

        self._logger.debug(f"Loaded {len(screen_ids)} IDs")
            

    def submit(self, metadata):
        self._logger.debug("Submitting a new task")

        metadata.backend.log_path = metadata.path.joinpath("backend.log")

        self.load_screens()
        old_ids = self._screen_ids

        if os.system(f"screen -L -Logfile '{metadata.backend.log_path}' -dmS 'SPMI screen {metadata.id}' {metadata.backend.command}") != 0:
            raise ScreenBackendException("Cannot start screen")

        self.load_screens()

        if len(old_ids) + 1 != len(self._screen_ids):
            raise ScreenBackendException("New screen is not started")

        screen_id = list(self._screen_ids - old_ids)[0]
        metadata.backend.id = screen_id

        self._logger.debug(f"New screen ID: {screen_id}")

    def _send(self, metadata, message):
        if not isinstance(message, str):
            raise TypeError(f"message must be str, not \"{type(message)}\"")

        self._logger.debug(f"Sending \"{message}\" to screen {metadata.backend.id}")
        self.load_screens()

        screen_id = metadata.backend.id

        if not self.is_active(metadata):
            raise ScreenBackendException(f"Attempting to operate on not existing screen \"{screen_id}\"")

        os.system(f"screen -x {screen_id} -X {message}")

    def term(self, metadata):
        self._send(metadata, "stuff '^C'")

    def kill(self, metadata):
        self._send(metadata, "quit")

    def is_active(self, metadata):
        self.load_screens()
        return metadata.backend.id in self._screen_ids
