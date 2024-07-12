"""Provides :class:`TaskManageable`.

Todo:
    Write documentation.
"""

import sys
import signal
import inspect
import logging
from pathlib import Path
from abc import ABCMeta, abstractmethod
from spmi.core.manageable import Manageable, manageable, ManageableException
from spmi.utils.metadata import MetaDataNode, MetaDataError
from spmi.utils.load import load_module
from spmi.utils.logger import Logger
from spmi.utils.exception import SpmiException

class TaskManageableException(ManageableException):
    pass

class BackendException(TaskManageableException):
    pass

@manageable
class TaskManageable(Manageable):
    """Manageable which handles a single command.

    Basic descriptor in TOML format:

    .. code-block:: TOML

        [task]                  # type of manageable
        id = "toml_task"        # ID of manageable

        [task.backend]          # backend section
        type = "screen"         # type of backend

        [task.wrapper]          # wrapper section
        type = "default"        # type of wrapper
        command = "sleep 10"    # command to execute

    """
    class MetaDataHelper(Manageable.MetaDataHelper):
        @property
        def backend(self):
            """:obj:`TaskManageable.Backend.MetaDataHelper`: Backend data.

            Raises:
                :class:`ValueError`
                :class:`TypeError`
            """
            if "backend" not in self.m_data:
                raise ValueError("Data should contain \"backend\" dictionary")
            if not isinstance(self.m_data["backend"], dict):
                raise TypeError(f"\"backend\" must be a dict, not {type(self.m_data['backend'])}")

            if "backend" not in self._meta:
                self._meta["backend"] = {}

            return TaskManageable.Backend.MetaDataHelper(
                data=self.m_data["backend"],
                meta=self._meta["backend"],
                copy=not self.mutable,
                mutable=self.mutable
            )

        @property
        def wrapper(self):
            """:obj:`TaskManageable.Wrapper.MetaDataHelper`: Wrapper data.

            Raises:
                :class:`ValueError`
                :class:`TypeError`
            """
            if "wrapper" not in self.m_data:
                raise ValueError("Data should contain \"wrapper\" dictionary")
            if not isinstance(self.m_data["wrapper"], dict):
                raise TypeError(f"\"wrapper\" must be a dict, not {type(self.m_data['wrapper'])}")

            if "wrapper" not in self._meta:
                self._meta["wrapper"] = {}

            return TaskManageable.Wrapper.MetaDataHelper(
                data=self.m_data["wrapper"],
                meta=self._meta["wrapper"],
                copy=not self.mutable,
                mutable=self.mutable
            )

        def __str__(self):
            return rf"""{super().__str__()}
backend:
{self.backend}
wrapper:
{self.wrapper}
"""


    class Backend(metaclass=ABCMeta):
        """Provides an interface to process manager.

        Any realisation should be defined in :py:mod:`spmi.core.manageables.task_.backends`
        package in own file.
        Its name should be written in PascalCase and ended with "Backend".
        """
        class MetaDataHelper(MetaDataNode):
            """Provides access to data."""
            @property
            def type(self):
                """:obj:`str`. Backend type."""
                return self._data["type"]

            @property
            def id(self):
                """:obj:`str`: ID of backend proces.

                Raises:
                    :class:`TypeError`
                    :class:`MetaDataError`
                """
                if "id" in self._meta:
                    return self._meta["id"]
                return None

            @id.setter
            def id(self, value):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                if not (value is None or isinstance(value, str)):
                    raise TypeError(f"value must be None or str, not {type(value)}")
                self._meta["id"] = value

            @property
            def command(self):
                """:obj:`str`: Start command.

                Raises:
                    :class:`TypeError`
                    :class:`MetaDataError`
                """
                if "start_command" in self._meta:
                    return self._meta["start_command"]
                return None

            @command.setter
            def command(self, value):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                if not (value is None or isinstance(value, str)):
                    raise TypeError(f"value must be None or str, not {type(value)}")
                self._meta["start_command"] = value

            @property
            def log_path(self):
                """:obj:`Union[pathlib.Path, None]`: Path to backend log file.
                ``None`` if there is no backend log file.

                Raises:
                    :class:`TypeError`
                    :class:`MetaDataError`
                """
                if "log_path" in self._meta and self._meta["log_path"]:
                    return Path(self._meta["log_path"])
                return None

            @log_path.setter
            def log_path(self, value):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                if not (value is None or isinstance(value, Path)):
                    raise TypeError(f"value must be None or pathlib.Path, not {type(value)}")
                self._meta["log_path"] = None if value is None else str(value.resolve())

            def __str__(self):
                return rf"""type: {self.type}
job id: {self.id}
log path: {self.log_path}
"""


        class LoadHelper:
            """Helps to load classes."""
            @staticmethod
            def get_class_name(string):
                """Converts ``string`` to class name.

                Args:
                    string (:obj:`str`): String.

                Returns:
                    :obj:`str`.
                """
                return string.capitalize() + "Backend"

            @staticmethod
            def get_backend(metadata):
                """Returns backend.

                Args:
                    task_metadata (:obj:`TaskManageable.MetaDataHelper`): Metadata.

                Returns:
                    :obj:`TaskManageable.Backend`.

                Raises:
                    :class:`NotImplementedError`
                """
                for path in Path(__file__).parent.joinpath("task_/backends").iterdir():
                    if path.is_file():
                        module_name = f"_task_backend_realisation_{path.stem}"
                        module = load_module(module_name, path)

                        classes = list(
                            filter(
                                lambda x: x[0] == TaskManageable.Backend.LoadHelper.get_class_name(
                                    metadata.backend.type
                                ),
                                inspect.getmembers(module)
                            )
                        )

                        if len(classes) == 1:
                            return classes[0][1]()

                raise NotImplementedError()

        @abstractmethod
        def submit(self, task_metadata):
            """Submits command.

            Args:
                task_metadata (:obj:`TaskManageable.MetaDataHelper`): Metadata.

            Returns:
                :obj:`str`. ID of submitted task.

            Raises:
                :class:`BackendException`
            """
            raise NotImplementedError()

        @abstractmethod
        def term(self, task_metadata):
            """Terminates wrapper process.

            Args:
                task_metadata (:obj:`TaskManageable.MetaDataHelper`): Metadata.

            Raises:
                :class:`BackendException`
            """
            raise NotImplementedError()

        @abstractmethod
        def kill(self, task_metadata):
            """Kills wrapper process.

            Args:
                task_metadata (:obj:`TaskManageable.MetaDataHelper`): Metadata.

            Raises:
                :class:`BackendException`
            """
            raise NotImplementedError()

        @abstractmethod
        def is_active(self, task_metadata):
            """Returns ``True``, if job is active.

            Args:
                task_metadata (:obj:`TaskManageable.MetaDataHelper`): Metadata.
            
            Returns:
                :obj:`bool`.

            Raises:
                :class:`BackendException`
            """
            raise NotImplementedError()

        @staticmethod
        def get_backend(task_metadata):
            """Returns backend.

            Args:
                task_metadata (:obj:`TaskManageable.MetaDataHelper`): Metadata.

            Returns:
                :obj:`TaskManageable.Backend`.

            Raises:
                :class:`NotImplementedError`
            """
            return TaskManageable.Backend.LoadHelper.get_backend(task_metadata)


    class Wrapper(metaclass=ABCMeta):
        """Class which handles a command execution.

        Any realisation should be defined in :py:mod:`spmi.core.manageables.task_.wrappers`
        package in own file.
        Its name should be written in PascalCase and ended with "Wrapper".
        """
        @abstractmethod
        def __init__(self, metadata=None):
            self._logger = Logger(self.__class__.__name__)
            self._metadata = metadata

        class MetaDataHelper(MetaDataNode):
            @property
            def type(self) -> str:
                """:obj:`str`: Wrapper type."""
                return self._data["type"]

            @property
            def command(self):
                """:obj:`str`: Wrapper type."""
                return self._data["command"]

            @property
            def mixed_stdout(self):
                """:obj:`bool`: ``True`` if stdout and stderr are one file.

                Raises:
                    :class:`MetaDataError`
                    :class:`TypeError`
                """
                return self._data["mixed_stdout"]

            @mixed_stdout.setter
            def mixed_stdout(self, value):
                if not self.mutable:
                    raise MetaDataError("Muste be mutable")
                if not isinstance(value, bool):
                    raise TypeError(f"value must be bool, not {type(value)}")
                self._data["mixed_stdout"] = value

            @property
            def stdout_path(self):
                """:obj:`Union[pathlib.Path, None]`: Path to backend stdout file.
                ``None`` if there is no backend stdout file.

                Raises:
                    :class:`MetaDataError`
                    :class:`TypeError`
                """
                if "stdout_path" in self._meta and self._meta["stdout_path"]:
                    return Path(self._meta["stdout_path"])
                return None

            @stdout_path.setter
            def stdout_path(self, value):
                if not self.mutable:
                    raise MetaDataError("Muste be mutable")
                if not (value is None or isinstance(value, Path)):
                    raise TypeError(f"value must be None or pathlib.Path, not {type(value)}")
                self._meta["stdout_path"] = None if value is None else str(value.resolve())

            @property
            def stderr_path(self):
                """:obj:`Union[pathlib.Path, None]`: Path to wrapper stderr file.
                ``None`` if there is no wrapper stderr file.

                Raises:
                    :class:`MetaDataError`
                    :class:`TypeError`
                """
                if self.mixed_stdout:
                    return self.stdout_path
                if "stderr_path" in self._meta and self._meta["stderr_path"]:
                    return Path(self._meta["stderr_path"])
                return None

            @stderr_path.setter
            def stderr_path(self, value):
                if not self.mutable:
                    raise MetaDataError("Muste be mutable")
                if not (value is None or isinstance(value, Path)):
                    raise TypeError(f"value must be None or pathlib.Path, not {type(value)}")
                self._meta["stderr_path"] = None if value is None else str(value.resolve())


            @property
            def stdin_path(self):
                """:obj:`Union[pathlib.Path, None]`: Path to wrapper stdin file.
                ``None`` if there is no wrapper stdin file.

                Raises:
                    :class:`MetaDataError`
                    :class:`TypeError`
                """
                if "stdin_path" in self._meta and self._meta["stdin_path"]:
                    return Path(self._meta["stdin_path"])
                return None

            @stdin_path.setter
            def stdin_path(self, value):
                if not self.mutable:
                    raise MetaDataError("Muste be mutable")
                if not (value is None or isinstance(value, Path)):
                    raise TypeError(f"value must be None or pathlib.Path, not {type(value)}")
                self._meta["stdin_path"] = None if value is None else str(value.resolve())

            @property
            def process_pid(self):
                """:obj:`Union[int, None]`: PID of wrapped process.
                ``None`` if process hasn't started.

                Raises:
                    :class:`MetaDataError`
                    :class:`TypeError`
                """
                if "process_pid" in self._meta and self._meta["process_pid"]:
                    return self._meta["process_pid"]
                return None

            @process_pid.setter
            def process_pid(self, value):
                if not self.mutable:
                    raise MetaDataError("Muste be mutable")
                if not (value is None or isinstance(value, int)):
                    raise TypeError(f"value must be None or int, not {type(value)}")
                self._meta["process_pid"] = value

            @property
            def exit_code(self):
                """:obj:`Union[int, None]`: Exit code of wrapped process.
                ``None`` if process hasn't finished.

                Raises:
                    :class:`MetaDataError`
                    :class:`TypeError`
                """
                if "exit_code" in self._meta and not self._meta["exit_code"] is None:
                    return self._meta["exit_code"]
                return None

            @exit_code.setter
            def exit_code(self, value):
                if not self.mutable:
                    raise MetaDataError("Muste be mutable")
                if not (value is None or isinstance(value, int)):
                    raise TypeError(f"value must be None or int, not {type(value)}")
                self._meta["exit_code"] = value

            def __str__(self):
                return rf"""type: {self.type}
command: {self.command}
stdin path: {self.stdin_path}
stdout path: {self.stdout_path}
stderr path: {self.stderr_path}
PID: {self.process_pid}
exit_code: {self.exit_code}
"""


        class LoadHelper:
            """Helps to load classes."""
            @staticmethod
            def get_class_name(string):
                """Converts ``string`` to class name.

                Args:
                    string (:obj:`str`): String.

                Returns:
                    :obj:`str`.
                """
                return string.capitalize() + "Wrapper"

            @staticmethod
            def get_wrapper(metadata):
                """Returns Wrapper.

                Args:
                    metadata (:obj:`TaskManageable.MetaDataHelper`): Metadata.

                Returns:
                    :obj:`TaskManageable.Wrapper`.

                Raises:
                    :class:`NotImplementedError`
                """
                for path in Path(__file__).parent.joinpath("task_/wrappers").iterdir():
                    if path.is_file():
                        module_name = f"_task_wrapper_realisation_{path.stem}"
                        module = load_module(module_name, path)

                        classes = list(
                            filter(
                                lambda x: x[0] == TaskManageable.Wrapper.LoadHelper.get_class_name(
                                    metadata.wrapper.type
                                ),
                                inspect.getmembers(module)
                            )
                        )

                        if len(classes) == 1:
                            return classes[0][1](metadata=metadata)

                raise NotImplementedError()


        @abstractmethod
        def start(self):
            """Start wrapper."""
            raise NotImplementedError()

        @abstractmethod
        def on_signal(self, signal, frame):
            """Called on signal."""
            raise NotImplementedError()

        @staticmethod
        def get_wrapper(metadata):
            """Loads wrapper.

            Raises:
                :class:`NotImplementedError`
            """
            return TaskManageable.Wrapper.LoadHelper.get_wrapper(metadata)

    class Cli:
        """CLI for wrapper."""
        @staticmethod
        def command(task_metadata):
            """Start command.

            Args:
                task_metadata (:obj:`TaskManageable.MetaDataHelper`): Metadata.

            Returns:
                :obj:`str`.

            Raises:
                :class:`ValueError`
            """
            if "'" in str(task_metadata.data_path):
                raise ValueError(f"Data path \"{task_metadata.data_path}\" must not contain \"'\"")
            if "'" in str(task_metadata.meta_path):
                raise ValueError(f"Meta path \"{task_metadata.meta_path}\" must not contain \"'\"")
            result = f"/usr/bin/env python3 '{__file__}' '{task_metadata.data_path}' '{task_metadata.meta_path}'"
            if Logger.log_level == logging.DEBUG:
                result += " debug"

            return result

        @staticmethod
        def from_args():
            """Load metadata from start command."""
            datapath = Path(sys.argv[1])
            metapath = Path(sys.argv[2])

            return TaskManageable.MetaDataHelper(data=datapath, meta=metapath)

    def __init__(self, *args, **kwargs):
        self._backend = TaskManageable.Backend.get_backend(self._metadata)

    def start(self):
        if self.active:
            raise TaskManageableException("Cannot start active task")
        self._metadata.backend.command = TaskManageable.Cli.command(self._metadata)
        self._backend.submit(self._metadata)

    def term(self):
        if not self.active:
            raise TaskManageableException("Cannot terminate inactive task")
        self._backend.term(self._metadata)

    def kill(self):
        if not self.active:
            raise TaskManageableException("Cannot kill inactive task")
        self._backend.kill(self._metadata)

    @property
    def active(self):
        return self._backend.is_active(self._metadata)

    def destruct(self):
        super().destruct()


def set_signal_handlers(wrapper):
    """Sets signal handlers."""
    for i in filter(lambda x: x.startswith("SIG"), dir(signal)):
        try:
            signum = getattr(signal, i)
            signal.signal(signum, wrapper.on_signal)
        except (OSError, ValueError):
            continue

if __name__ == "__main__":
    Logger.basic_config(loglevel="DEBUG" if "debug" in sys.argv else "INFO")
    metadata = TaskManageable.Cli.from_args()
    wrapper = TaskManageable.Wrapper.get_wrapper(metadata)
    set_signal_handlers(wrapper)
    wrapper.start()
