import toml
from pathlib import Path
from filelock import FileLock
from ..descriptor import Descriptor

class Io(Descriptor.Io):
    def __init__(self, path: Path, lock: bool):
        assert path.exist()
        self.path = path
        self.lock = FileLock(path.with_suffix("lock")) if lock else None
        self.load()


    def _acquire(self):
        if self.lock: self.lock.acquire()


    def _release(self):
        if self.lock: self.lock.release()

    
    def load(self) -> dict:
        self._acquire()

        with open(self.path, "r") as f:
            dictionary = toml.load(f)

        self._release()

        return dictionary


    def dump(self, descriptor: dict):
        if self.lock: self.lock.acquire()

        with open(self.path, "w") as f:
            toml.dump(dict, f)
        
        if self.lock: self.lock.release()

