import importlib
import inspect
from abc import ABCMeta, abstractmethod

class Backend(metaclass=ABCMeta):
    """Backend"""

    @abstractmethod
    def submit(self, task):
        pass

    @abstractmethod
    def cancel(self, task):
        pass

    @abstractmethod
    def is_active(self, task):
        pass

    @staticmethod
    def get_backend(id: str):
        return 10

        if id == "backend":
            raise BackendException("Invalid backend id")

        module = importlib.import_module(id)

        return filter(lambda x: inspect.isclass(x) and issubclass(x, Backend), inspect.getmembers(module))[0]
