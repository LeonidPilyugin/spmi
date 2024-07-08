"""
.. module:: default.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import os
from spmi.core.manageables.task import TaskManageable

@TaskManageable.wrapper
class DefaultWrapper(TaskManageable.Wrapper):
    def start(self):
        os.system(self._metadata.wrapper.command)

    def on_signal(self, signal, frame):
        print(f"Got signal: {signal}")

    def finish(self):
        print("Wrapper finished")



