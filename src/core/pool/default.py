from pathlib import Path
import subprocess
import shutil
import toml
from .realisation import Realisation as AbstractRealisation
from ..task import Task
from ..pool import Pool
from ..cover import Cover
from ..utils import Logger
from ..descriptor.descriptor import Descriptor

class Pool(Pool):
    """
    Default implementation of Pool
    """

    def __init__(self, directory: Path):
        self.logger = Logger("Pool")


        self.logger.debug("Setting directory")
        self.directory = directory

        if not self.directory.exists():
            self.logger.info(f"Directory {str(directory)} doesn't exist. Creating it.")
            self.directory.mkdir()

        self.logger.debug("Directory is set")

        self.load_all()


    def load_all(self):
        """
        Load all tasks
        """
        self.logger.debug("Loading tasks")
        self.tasks = [self.load_task(p) for p in self.directory.rglob("*") if p.is_dir()]
        logger.debug("Tasks are loaded")


    def load_task(self, directory: Path) -> Task:
        """
        Loads already created task from directory
        """
        assert directory.exists()

        descriptor_path = [d for d in directory.glob("descriptor.*") if not d.suffix == ".lock"]
        assert len(descriptor_path) == 1
        descriptor_path = descriptor_path[0]
        
        descriptor = Descriptor.load_descriptor(descriptor_path.suffix()[1:], descriptor_path, lock=True)

        return Task(descriptor)


    def create_task(self, descriptor: Path) -> Task:
        task_id = self.generate_id()

        directory = self.directory.joinpath(task_id)
        directory.mkdir()

        descriptor_type = descriptor.suffix()[1:]

        self.logger.debug("Creating task directory")

        directory = self.directory.joinpath(task_id)
        descriptor_path = directory.joinpath(f"descriptor.{descriptor_type}")

        shutil.copyfile(descriptor, descriptor_path)

        descriptor_object = Descriptor.load_descriptor(descriptor_type, descriptor_path, True)

        descriptor_object["id"] = task_id
        descriptor_object["dir"] = str(directory)

        # TODO get wrapper from descriptor
        command = Cover.Command(__file__, str(directory.joinpath("process.log")), descriptor_object["command"])
        descriptor_object["wrapper_command"] = Cover.start_command(command)
        
        task = Task(descriptor_object)
        self.tasks.append(task)

        return task


    def remove_task(self, task: Task, force=False):
        task.stop()
        shutil.rmtree(Path(task.descriptor["dir"]))



    def generate_id(self):
        """
        Generates a new id
        """
        
        task_id = None

        while not task_id or task_id in [t.state["id"] for t in self.tasks]:
            task_id = os.urandom(self.id_length).hex()

        return task_id

