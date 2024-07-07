import screenutils
from backend import Backend
from ...utils.hash import generate_hash

class ScreenBackend(Backend):

    class TaskMetaHelper:
        def __init__(self, task: Task):
            self.task = task
            if not "backend" in self.task.meta.data:
                self.task.meta.data["backend"] = {}
                self.data["id"] = "screen"

        @property
        def data(self):
            return self.task.meta.data["backend"]

        @property
        def hash(self):
            return self.data["hash"]
        
        @hash.setter
        def set_hash(self, value):
            self.data["hash"] = value

    HASH_SIZE = 16


    @classmethod
    def load_screens(cls):
        cls.screens = screenutils.load_screens()

    @classmethod
    def generate_hash(cls):
        result_hash = None

        while result_hash is None or result_hash in list(map(lambda x: x.name, cls.screens)):
            result_hash = generate_hash(size=cls.HASH_SIZE)
        
        return result_hash
        
    
    @classmethod
    def submit(cls, task: Task):
        cls.load_screens()

        th = ScreenBackend.TaskMetaHelper(task)
        th.hash = ScreenBackend.generate_hash()


    @classmethod
    def cancel(cls, task: Task):
        cls.load_screens()

    @classmethod
    def is_active(cls, task: Task):
        cls.load_screens()
