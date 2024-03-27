import subprocess
from .backend import Backend as AbstractBackend
from ..descriptor.descriptor import Descriptor

class Backend(AbstractBackend):
    """
    Provides an API for screen
    """

    SESSION_NAME_TEMPLATE = "pls_screen_session_{id}"
    SHELL_START_COMMAND_TEMPLATE = "screen -dmS {name} {process}"
    SHELL_STOP_COMMAND_TEMPLATE = "screen -X -S {name} quit"

    @staticmethod
    def submit(descriptor: Descriptor):
        task_id = descriptor["id"]
        wrapper_process = descriptor["wrapper_process"]

        # TODO check if such process is already running
        
        session_name = Backend.SESSION_NAME_TEMPLATE.format(id=task_id)
        command = Backend.SHELL_START_COMMAND_TEMPLATE.format(name=session_name, process=wrapper_process)

        p = subprocess.Popen(command, shell=True)
        p.wait()

        descriptor["backend"]["status"] = "started"
        descriptor["backend"]["session_name"] = session_name

    @staticmethod
    def cancel(descriptor: Descriptor):
        session_name = descriptor["backend"]["session_name"]

        command = Backend.SHELL_STOP_COMMAND_TEMPLATE.format(name=session_name)
        p = subprocess.Popen(command, shell=True)
        p.wait()

        descriptor["backend"]["status"] = "canceled"




