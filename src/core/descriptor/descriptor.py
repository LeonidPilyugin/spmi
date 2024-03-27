from abc import ABCMeta, abstractmethod
import importlib
import sys

class Descriptor:
    """
    A class which describes a task: stores it's id, process, log path and other info.
    """

    class Io(metaclass=ABCMeta):
        """
        Can load and dump descriptor
        """
        
        @abstractmethod
        def load(self) -> dict:
            """
            Loads descriptor 
            """
            pass

        @abstractmethod
        def dump(self, descriptor: dict):
            """
            Dumps descriptor
            """
            pass

    def __init__(self, io: Descriptor.Io):
        assert isinstance(io, Descriptor.Io)
        self.io = io

    def load(self):
        self.dict = self.io.load()

    def dump(self):
        self.io.dump(self.dict)

    # TODO dict methods
    # TODO id getter/setter
    # TODO log getter/setter

def load_descriptor(path: Path, lock: bool = True) -> Descriptor:
    """
    Loads descriptor by file path
    """

    module = importlib.import_module(f".io.{path.suffix()[1:])}")
    return Descriptor(module.Io(path, lock))
