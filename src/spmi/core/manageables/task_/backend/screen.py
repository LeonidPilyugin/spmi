"""
.. module:: screen.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import screenutils
from spmi.core.manageables.task import TaskManageable

class ScreenBackend(TaskManageable.Backend):
    """Screen backend."""
    def __init__(self):
        self._screens = []
        self.load_screens()

    def load_screens(self):
        """Loads all screen sessions."""
        self._screens = screenutils.list_screens()

    def submit(self, metadata: TaskManageable.MetaDataHelper):
        screen = screenutils.Screen("SPMI task", True)
        screen_id = screen.id

        metadata.backend.id = screen_id
        screen.send_commands(metadata.backend.command)
        screen.detach()

    def cancel(self, metadata: TaskManageable.MetaDataHelper):
        self.load_screens()

        screen_id = metadata.backend.id
        assert screen_id
        assert self.is_active(metadata)

        screen = list(
            filter(
                lambda x: x.id == screen_id,
                self._screens
            )
        )[0]

        screen.kill()

    def is_active(self, metadata: TaskManageable.MetaDataHelper):
        self.load_screens()
        return metadata.backend.id in map(lambda x: x.id, self._screens)
