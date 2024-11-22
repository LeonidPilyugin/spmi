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
            for l in subprocess.getoutput("screen -ls").split("\n")
            if "\t" in l and ".".join(l.split(".")[1:]).split("\t")[0]
        ]

        self._screen_ids = set(screen_ids)

        if len(self._screen_ids) != len(screen_ids):
            raise ScreenBackendException('Found equal IDs in "screen -ls"')

        self._logger.debug(f"Loaded {len(screen_ids)} IDs")

    def submit(self, task_metadata):
        super().submit(task_metadata)
        self._logger.debug("Submitting a new task")

        task_metadata.backend.log_path = task_metadata.path.joinpath("backend.log")

        self.load_screens()
        old_ids = self._screen_ids

        if (
            os.system(
                f"screen -L -Logfile '{task_metadata.backend.log_path}' -dmS 'SPMI screen {task_metadata.id}' {task_metadata.backend.command}"
            )
            != 0
        ):
            raise ScreenBackendException("Cannot start screen")

        self.load_screens()

        if len(old_ids) + 1 != len(self._screen_ids):
            raise ScreenBackendException("New screen is not started")

        screen_id = list(self._screen_ids - old_ids)[0]
        task_metadata.backend.id = screen_id

        self._logger.debug(f"New screen ID: {screen_id}")

    def _send(self, task_metadata, message):
        if not isinstance(message, str):
            raise TypeError(f'message must be str, not "{type(message)}"')

        self._logger.debug(f'Sending "{message}" to screen {task_metadata.backend.id}')
        self.load_screens()

        screen_id = task_metadata.backend.id

        if not self.is_active(task_metadata):
            raise ScreenBackendException(
                f'Attempting to operate on not existing screen "{screen_id}"'
            )

        command = f"screen -x {screen_id} -X {message}"
        if os.system(command) != 0:
            raise ScreenBackendException(f'Command  "{command}" failed')

    def term(self, task_metadata):
        super().term(task_metadata)
        self._send(task_metadata, "stuff '^C'")

    def kill(self, task_metadata):
        super().kill(task_metadata)
        self._send(task_metadata, "quit")

    def is_active(self, task_metadata):
        super().is_active(task_metadata)
        self.load_screens()
        return task_metadata.backend.id in self._screen_ids
