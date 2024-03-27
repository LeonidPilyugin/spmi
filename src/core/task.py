from abc import ABCMeta, abstractmethod
from .utils.logger import Logger
from .cover import Cover
from .backend.backend import Backend


class Task:
    """
    Manages a single task.
    """
    def __init__(self, descriptor: Descriptor):
        self.logger = Logger("Task")

        self.logger.debug("Creating Task object")

        self.logger.debug("Checking arguments")
        assert isinstance(descriptor, Task.Descriptor)
        self.logger.debug("Arguments are OK")
        
        self.descriptor = descriptor
        
        self.backend = Backend.get_backend(self.descriptor["backend"]["type"], self.descriptor["backend"])


    def load(self):
        """
        Loads descriptor
        """
        
        self.logger.debug("Reloading descriptor")
        self.descriptor.load()
        self.logger.debug("Descriptor reloaded")


    def dump(self):
        """
        Dumps descriptor
        """
        
        self.logger.debug("Dumping descriptor")
        self.descriptor.dump()
        self.logger.debug("Descriptor dumped")


    def start(self):
        """
        Starts a new task
        """
        self.backend.submit(self.descriptor)


    def stop(self):
        """
        Stops already started task
        """
        self.backend.cancel(self.descriptor)


