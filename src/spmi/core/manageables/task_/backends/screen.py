"""Provides :class:`ScreenBackend`.
"""

import os
import subprocess
from spmi.core.manageables.task import TaskManageable
from spmi.utils.logger import Logger

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

        assert len(self._screen_ids) == len(screen_ids)

        self._logger.debug(f"Loaded {len(screen_ids)} IDs")
            

    def submit(self, metadata):
        self._logger.debug("Submitting a new task")

        metadata.backend.log_path = metadata.path.joinpath("backend.log")

        self.load_screens()
        old_ids = self._screen_ids

        assert os.system(f"screen -L -Logfile '{metadata.backend.log_path}' -dmS 'SPMI screen' {metadata.backend.command}") == 0

        self.load_screens()
        assert len(old_ids) + 1 == len(self._screen_ids)
        screen_id = list(self._screen_ids - old_ids)[0]
        metadata.backend.id = screen_id

        self._logger.debug(f"New screen ID: {screen_id}")

    def cancel(self, metadata):
        self._logger.debug(f"Canceling screen {metadata.backend.id}")
        self.load_screens()

        screen_id = metadata.backend.id
        assert screen_id
        assert self.is_active(metadata)

        os.system(f"screen -x {screen_id} -X quit")

    def is_active(self, metadata):
        self.load_screens()
        return metadata.backend.id in self._screen_ids
