import importlib
from abc import ABCMeta, abstractmethod

class Pool(metaclass=ABCMeta):
    """
    A class which manages list of tasks
    """

    @abstractmethod
    def create_task(self, descriptor):
        """Create a new task"""
        pass

    @abstractmethod
    def remove_task(self, tid):
        pass

    @property
    @abstractmethod
    def tasks(self):
        """A list of tasks"""
        pass

def load_pool(pool: str, directory: Path):
    module = importlib.import_module(f".{pool}")
    return module.Pool(directory)

