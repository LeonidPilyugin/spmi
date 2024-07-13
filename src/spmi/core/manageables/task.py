"""Provides :class:`TaskManageable`.

Todo:
    Write documentation.
"""

import os
import sys
import signal
import inspect
import logging
from datetime import datetime
from pathlib import Path
from subprocess import getoutput
from abc import ABCMeta, abstractmethod
from spmi.core.manageable import Manageable, manageable, ManageableException
from spmi.utils.metadata import MetaDataNode, MetaDataError, dontcheck
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
        def _backend(self, cls):
            if "backend" not in self.m_data:
                raise ValueError("Data should contain \"backend\" dictionary")
            if not isinstance(self.m_data["backend"], dict):
                raise TypeError(f"\"backend\" must be a dict, not {type(self.m_data['backend'])}")

            if "backend" not in self._meta:
                self._meta["backend"] = {}

            return cls.MetaDataHelper(
                data=self.m_data["backend"],
                meta=self._meta["backend"],
                copy=not self.mutable,
                mutable=self.mutable
            )

        @property
        def backend(self):
            """:obj:`TaskManageable.Backend.MetaDataHelper`: Backend data.

            Raises:
                :class:`ValueError`
                :class:`TypeError`
            """
            if not hasattr(self, "_backend_class"):
                self._backend_class = TaskManageable.Backend.LoadHelper.get_backend(self)
            return self._backend(self._backend_class)

        @property
        def common_backend(self):
            return self._backend(TaskManageable.Backend)

        def _wrapper(self, cls):
            if "wrapper" not in self.m_data:
                raise ValueError("Data should contain \"wrapper\" dictionary")
            if not isinstance(self.m_data["wrapper"], dict):
                raise TypeError(f"\"wrapper\" must be a dict, not {type(self.m_data['wrapper'])}")

            if "wrapper" not in self._meta:
                self._meta["wrapper"] = {}

            return cls.MetaDataHelper(
                data=self.m_data["wrapper"],
                meta=self._meta["wrapper"],
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
            if not hasattr(self, "_wrapper_class"):
                self._wrapper_class = TaskManageable.Wrapper.get_wrapper(self)
            return self._wrapper(self._wrapper_class)

        @property
        def common_wrapper(self):
            return self._wrapper(TaskManageable.Wrapper)

        def reset(self):
            super().reset()
            self.backend.reset()
            self.wrapper.reset()


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

            @id.deleter
            def id(self):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                del self._meta["id"]

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

            @command.deleter
            def command(self):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                del self ["start_command"]

            @dontcheck
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

            @log_path.deleter
            def log_path(self):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                assert "log_path" in self._meta
                if self.log_path.exists():
                    self.log_path.unlink()
                del self._meta["log_path"]

            def reset(self):
                if self.log_path: del self.log_path
                if not self.id is None: del self.id


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
                                    metadata.common_backend.type
                                ),
                                inspect.getmembers(module)
                            )
                        )

                        if len(classes) == 1:
                            return classes[0][1]

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

            @dontcheck
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
                    raise MetaDataError("Must be mutable")
                if not (value is None or isinstance(value, Path)):
                    raise TypeError(f"value must be None or pathlib.Path, not {type(value)}")
                self._meta["stdout_path"] = None if value is None else str(value.resolve())

            @stdout_path.deleter
            def stdout_path(self):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                assert "stdout_path" in self._meta
                if self.stdout_path.exists():
                    self.stdout_path.unlink()
                del self._meta["stdout_path"]

            @dontcheck
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
                    raise MetaDataError("Must be mutable")
                if not (value is None or isinstance(value, Path)):
                    raise TypeError(f"value must be None or pathlib.Path, not {type(value)}")
                self._meta["stderr_path"] = None if value is None else str(value.resolve())

            @stderr_path.deleter
            def stderr_path(self):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                assert "stderr_path" in self._meta
                if self.stderr_path.exists():
                    self.stderr_path.unlink()
                del self._meta["stderr_path"]

            @dontcheck
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
                    raise MetaDataError("Must be mutable")
                if not (value is None or isinstance(value, Path)):
                    raise TypeError(f"value must be None or pathlib.Path, not {type(value)}")
                self._meta["stdin_path"] = None if value is None else str(value.resolve())

                if value:
                    os.mkfifo(value)

            @stdin_path.deleter
            def stdin_path(self):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")

                assert "stdin_path" in self._meta
                if self.stdin_path:
                    os.unlink(self.stdin_path)
                del self._meta["stdin_path"]

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
                    raise MetaDataError("Must be mutable")
                if not (value is None or isinstance(value, int)):
                    raise TypeError(f"value must be None or int, not {type(value)}")
                self._meta["process_pid"] = value

            @process_pid.deleter
            def process_pid(self):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                del self._meta["process_pid"]

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
                    raise MetaDataError("Must be mutable")
                if not (value is None or isinstance(value, int)):
                    raise TypeError(f"value must be None or int, not {type(value)}")
                self._meta["exit_code"] = value

            @exit_code.deleter
            def exit_code(self):
                if not self.mutable:
                    raise MetaDataError("Must be mutable")
                del self._meta["exit_code"]

            def reset(self):
                if self.stdin_path: del self.stdin_path
                if self.stdout_path: del self.stdout_path
                if self.stderr_path and self.mixed_stdout: del self.stderr_path
                if not self.exit_code is None: del self.exit_code
                if not self.process_pid is None: del self.process_pid


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
                                    metadata.common_wrapper.type
                                ),
                                inspect.getmembers(module)
                            )
                        )

                        if len(classes) == 1:
                            return classes[0][1]

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
            if Logger.log_level() == logging.DEBUG:
                result += " debug"

            return result

        @staticmethod
        def from_args():
            """Load metadata from start command."""
            datapath = Path(sys.argv[1])
            metapath = Path(sys.argv[2])

            return TaskManageable.MetaDataHelper(data=datapath, meta=metapath)

    def __init__(self, *args, **kwargs):
        self._backend = TaskManageable.Backend.get_backend(self._metadata)()

    def start(self):
        super().start()
        self._metadata.backend.command = TaskManageable.Cli.command(self._metadata)
        self._backend.submit(self._metadata)
        self._metadata.start_time = datetime.now()

    def term(self):
        super().term()
        self._backend.term(self._metadata)
        self._metadata.finish_time = datetime.now()

    def kill(self):
        super().kill()
        self._backend.kill(self._metadata)
        self._metadata.finish_time = datetime.now()

    @property
    def active(self):
        return self._backend.is_active(self._metadata)

    def destruct(self):
        super().destruct()
        
    def status_string(self, align=0):
        """Returns status string of this manageable.

        Args:
            align (:obj:`int`): Align.
        """
        align = max(
            align,
            max(
                map(
                    lambda x: len(x),
                    [
                        "Backend type",
                        "Backend ID",
                        "Wrapper type",
                        "Command",
                        "PID",
                        "Exit code",
                    ]
                )
            )
        )

        state = self.state
        result = super().status_string(align=align)
        result += f"{{:>{align}}}: {{:}}\n".format("Backend type", state.backend.type)
        if state.backend.id:
            result += f"{{:>{align}}}: {{:}}\n".format("Backend ID", state.backend.id)
        result += f"{{:>{align}}}: {{:}}\n".format("Wrapper type", state.wrapper.type)
        result += f"{{:>{align}}}: {{:}}\n".format("Command", state.wrapper.command)
        if isinstance(state.wrapper.process_pid, int):
            result += f"{{:>{align}}}: {{:}}\n".format("PID", state.wrapper.process_pid)
        if isinstance(state.wrapper.exit_code, int):
            result += f"{{:>{align}}}: {{:}}\n".format("Exit code", state.wrapper.exit_code)

        if isinstance(state.wrapper.stdout_path, Path):
            result += "\n"
            result += getoutput(f"tail -5 {state.wrapper.stdout_path}")
            result += "\n"

        return result


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
    wrapper = TaskManageable.Wrapper.get_wrapper(metadata)(metadata=metadata)
    set_signal_handlers(wrapper)
    wrapper.start()
