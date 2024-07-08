"""
.. module:: task.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""

import sys
import signal
import inspect
from pathlib import Path
from abc import ABCMeta, abstractmethod
from spmi.core.manageable import Manageable, manageable
from spmi.utils.metadata import SubDict
from spmi.utils.load import load_module

@manageable
class TaskManageable(Manageable):
    """TaskManageable. Manageable which handles a single command."""
    class MetaDataHelper(Manageable.MetaDataHelper):
        """Provides access to meta and data."""
        @property
        def backend(self):
            """Backend data."""
            assert "backend" in self.m_data
            assert isinstance(self.m_data["backend"], dict)

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
            """Wrapper data."""
            assert "wrapper" in self.m_data
            assert isinstance(self.m_data["wrapper"], dict)

            if "wrapper" not in self._meta:
                self._meta["wrapper"] = {}

            return TaskManageable.Wrapper.MetaDataHelper(
                data=self.m_data["wrapper"],
                meta=self._meta["wrapper"],
                copy=not self.mutable,
                mutable=self.mutable
            )


    class Backend(metaclass=ABCMeta):
        """Backend"""
        class MetaDataHelper(SubDict):
            """Provides access to data."""
            @property
            def type(self) -> str:
                """str. Backend type."""
                return self._data["type"]

            @property
            def id(self) -> str | None:
                """str. Id of backend proces."""
                if "id" in self._meta:
                    return self._meta["id"]
                return None

            @id.setter
            def id(self, value: str | None):
                assert self.mutable
                assert value is None or isinstance(value, str)
                self._meta["id"] = value

            @property
            def command(self) -> str | None:
                """str. Start command."""
                if "start_command" in self._meta:
                    return self._meta["start_command"]
                return None

            @command.setter
            def command(self, value: str | None):
                assert self.mutable
                assert value is None or isinstance(value, str)
                self._meta["start_command"] = value


        class LoadHelper:
            """Helps to load classes."""
            @staticmethod
            def get_class_name(string: str) -> str:
                """Converts string to class name.

                Args:
                    string (str): string.

                Returns:
                    str.
                """
                return string.capitalize() + "Backend"

            @staticmethod
            def get_backend(metadata):
                """Returns backend by data dict.

                Args:
                    data (:obj:`dict`): Data dict.

                Returns:
                    :obj:`Backend`.
                """
                for path in Path(__file__).parent.joinpath("task_/backend").iterdir():
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

                        if len(classes) >= 1:
                            assert len(classes) == 1
                            return classes[0][1]()

                raise NotImplementedError()

        @abstractmethod
        def submit(self, task_metadata) -> str:
            """Submits command.

            Args:
                command (str): command to submit

            Returns:
                str. ID of submitted task.
            """
            raise NotImplementedError()

        @abstractmethod
        def cancel(self, task_metadata):
            """Canceles job by ID.

            Args:
                id (str): ID, returned by submit function.
            """
            raise NotImplementedError()

        @abstractmethod
        def is_active(self, task_metadata) -> bool:
            """Returns True, if job is active.

            Args:
                id (str): ID, returned by submit function.
            
            Returns:
                bool.
            """
            raise NotImplementedError()

        @staticmethod
        def get_backend(task_metadata):
            """Returns backend by data dict.

            Args:
                data (:obj:`dict`): Data dict.

            Returns:
                :obj:`Backend`.
            """
            return TaskManageable.Backend.LoadHelper.get_backend(task_metadata)

    @staticmethod
    def wrapper(wrap_class):
        """All wrappers should be decorated wtih it."""
        def __new_init__(self, *args, metadata=None, **kwargs):
            self._metadata = metadata

            if self.__old_init__:
                self.__old_init__(*args, metadata=metadata, **kwargs)

        wrap_class.__old_init__ = wrap_class.__init__
        wrap_class.__init__ = __new_init__

        return wrap_class

    @wrapper
    class Wrapper(metaclass=ABCMeta):
        """Class which handles a command execution."""
        class MetaDataHelper(SubDict):
            """Provides access to data."""
            @property
            def type(self) -> str:
                """str. Wrapper type."""
                return self._data["type"]

            @property
            def command(self) -> str:
                """str. Wrapper type."""
                return self._data["command"]


        class LoadHelper:
            """Helps to load classes."""
            @staticmethod
            def get_class_name(string: str) -> str:
                """Converts string to class name.

                Args:
                    string (str): string.

                Returns:
                    str.
                """
                return string.capitalize() + "Wrapper"

            @staticmethod
            def get_wrapper(metadata):
                """Returns backend by data dict.

                Args:
                    data (:obj:`dict`): Data dict.

                Returns:
                    :obj:`Backend`.
                """
                for path in Path(__file__).parent.joinpath("task_/wrapper").iterdir():
                    if path.is_file():
                        module_name = f"_task_wrapper_realisation_{path.stem}"
                        module = load_module(module_name, path)

                        classes = list(
                            filter(
                                lambda x: x[0] == TaskManageable.Wrapper.LoadHelper.get_class_name(
                                    metadata.backend.type
                                ),
                                inspect.getmembers(module)
                            )
                        )

                        if len(classes) >= 1:
                            assert len(classes) == 1
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

        @abstractmethod
        def finish(self):
            """Called on finish."""
            raise NotImplementedError()

        @staticmethod
        def get_wrapper(metadata):
            """Loads wrapper."""
            TaskManageable.Wrapper.LoadHelper.get_wrapper(metadata)

    class Cli:
        """CLI for wrapper."""
        @staticmethod
        def command(task_metadata) -> str:
            """Start command."""
            return f"/usr/bin/env python3 '{__file__}' '{task_metadata.data_path}' '{task_metadata.meta_path}'"

        @staticmethod
        def from_args():
            """Load metadata from start command"""
            datapath = Path(sys.argv[1])
            assert datapath.exists() and datapath.is_file()

            metapath = Path(sys.argv[2])
            assert metapath.exists() and metapath.is_file()

            return TaskManageable.MetaDataHelper(data=datapath, meta=metapath)

    def __init__(self, *args, **kwargs):
        self._backend = TaskManageable.Backend.get_backend(self._metadata)

    @property
    def is_active(self):
        return self._backend.is_active(self._metadata)

    def start(self):
        print("TODO: WHERE TO DUMP????")
        exit(1)
        self._metadata.backend.command = Manageable.Cli.command(self._metadata)
        self._backend.submit(self._metadata)

    def stop(self):
        self._backend.cancel(self._metadata)

def set_signal_handlers(wrapper):
    """Sets signal handlers."""
    for i in filter(lambda x: x.startswith("SIG"), dir(signal)):
        try:
            signum = getattr(signal, i)
            signal.signal(signum, wrapper.on_signal)
        except OSError:
            continue

if __name__ == "__main__":
    print("Main function")
    metadata = TaskManageable.Cli.from_args()
    wrapper = TaskManageable.Wrapper.get_wrapper(metadata)
    set_signal_handlers(wrapper)
    wrapper.start()
    wrapper.finish()
    print("finished")
