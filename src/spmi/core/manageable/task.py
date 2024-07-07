"""
.. module:: task.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

from pathlib import Path
from dataclasses import dataclass
from spmi.core.manageable.manageable import Manageable, ManageableState, manageable
from spmi.core.backend.backend import Backend
from spmi.core.wrapper.wrapper import Wrapper

@dataclass(frozen=True)
class TaskState(ManageableState):
    """Task immutable state.

    Args:
        exit_code (int): command exit code.
        log_path (str): path to log file.
        backend (str): backend type.
    """
    exit_code: int
    log_path: str
    backend: str
    wrapper: str
    command: str

@manageable
class Task(Manageable):
    """Task. Manageable which handles a single command."""
    class MetaDataHelper(Manageable.MetaDataHelper):
        """Provides access to meta and data."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            if "exit_code" not in self._meta.data:
                self.exit_code = None
            if "log_path" not in self._meta.data:
                self.log_path = None

            assert all([
                "exit_code" in self._meta.data,
                "log_path" in self._meta.data,
                "backend" in list(self._data.data.values())[0],
                "wrapper" in list(self._data.data.values())[0],
                "command" in self.wrapper,
                "type" in self.wrapper
            ])

        @property
        def exit_code(self) -> int:
            """int. Exit code of command."""
            return self._meta.data["exit_code"]

        @exit_code.setter
        def exit_code(self, value: int):
            assert value is None or isinstance(value, int)
            self._meta.data["exit_code"] = value

        @property
        def log_path(self) -> Path:
            """:obj:`Path`. Path of log file."""
            return self._meta.data["log_path"]

        @log_path.setter
        def log_path(self, value: Path):
            assert value is None or isinstance(value, Path)
            self._meta.data["log_path"] = value

        @property
        def backend(self) -> str:
            """str. Backend data."""
            return list(self._data.data.values())[0]["backend"]

        @property
        def wrapper(self) -> dict:
            """:obj:`dict`. Wrapper data."""
            return dict(list(self._data.data.values())[0]["wrapper"])

        @property
        def command(self) -> str:
            """str. Handled command."""
            return self.wrapper["command"]

        @property
        def wrapper_type(self) -> str:
            """str. Wrapper type."""
            return self.wrapper["type"]

        @property
        def state(self) -> TaskState:
            """:obj:`ManageableState` Copy to immutable state."""
            return TaskState(
                log_path=str(self.log_path),
                backend=self.backend,
                wrapper=self.wrapper,
                command=self.command,
                exit_code=self.exit_code,
                **super().state.dict(),
            )


    class FileSystemHelper(Manageable.FileSystemHelper):
        """File system helper."""
        LOG_FILE_NAME = "log.log"

        @classmethod
        def register(cls, manageable, path: Path):
            super().register(manageable, path)
            log_path = path.joinpath(Task.FileSystemHelper.LOG_FILE_NAME)
            log_path.touch()
            manageable.log_path = log_path

        @classmethod
        def is_correct_tree(cls, clz, path: Path) -> bool:
            return all([
                super().is_correct_tree(super(clz), path),
                path.joinpath(cls.LOG_FILE_NAME).exists(),
                path.joinpath(cls.LOG_FILE_NAME).is_file()
            ])

        @classmethod
        def from_tree(cls, clz, path: Path):
            manageable_kwargs = super().from_tree(clz, path)
            return Task(**manageable_kwargs)

    def __init__(self, *args, **kwargs):
        self._backend = Backend.get_backend(self._metadata.backend)
        self._wrapper = Wrapper.get_wrapper(self._metadata.wrapper)

    @property
    def is_active(self):
        return False

    def start(self):
        pass
        #self._backend.submit(self._metadata.id, self._wrapper.command)

    def stop(self):
        pass
        #self._backend.cancel(self._metadata.id)
