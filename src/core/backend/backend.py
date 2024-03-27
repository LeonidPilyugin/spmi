from abc import ABCMeta, abstractmethod
from ..descriptor.descriptor import Descriptor

class Backend(metaclass=ABCMeta):
    """
    Provides API for task manager e.g. slurm or screen
    """
    
    @staticmethod
    @abstractmethod
    def submit(descriptor):
        """
        Submits a new process
        """
        pass

    @staticmethod
    @abstrctmethod
    def cancel(descriptor: Descriptor):
        """
        Cancels running process
        """
        pass

    # @staticmethod
    # @abstractmethod
    # def is_alive(descriptor: Descriptor):
    #     """
    #     Returns true if process is running
    #     """
    #     pass


def get_backend(backend: str):
    """
    Loads backend by string id
    """

    module = importlib.import_module(f".{backend}")
    return module.Backend
