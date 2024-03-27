import signal
import sys
import importlib
import argparse
from abc import ABCMeta, abstractmethod
from pathlib import Path
from .utils.logger import Logger

class Cover:
    """
    Class which handles a started process
    """
    
    @staticmethod
    def start_command(command: Cover.Command):
        """
        Returns start command
        """
        
        return f"python3 {__file__} {str(command)}"    

logger = Logger("WrapperProcess")
logger.setLevel("INFO")

def load_wrapper_object(command: Cover.Command) -> Cover.Wrapper
    """
    Loads class
    """
    
    spec = importlib.util.spec_from_file_location(module_name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    return getattr(module, name)(command.command, command.log_file, logger)


def on_term(wrapper):
    logger.warning("Got SIGTERM")
    wrapper.on_term()
    logger.debug("Exiting SIGTERM handler")
    exit(1)


def on_int(wrapper):
    logger.warning("Got SIGINT")
    wrapper.on_term()
    logger.debug("Exiting SIGINT handler")
    exit(2)


if __name__ == "__main__"
    logger.info("Starting cover process")

    command = Cover.Command.from_string(" ".join(sys.argv[1:]))
    logger.logger.setLevel(command.log_level)

    logger.debug(f"Got arguments: {str(command)}")
    logger.debug("Loading wrapper")
    wrapper = load_wrapper_object(command)
    logger.debug("Wrapper loaded")
    
    logger.debug("Setting signals")
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_int)
    logger.debug("Signals are set")

    logger.debug("Starting process")
    wrapper.start()
    logger.debug("Process finished")

    logger.info("Wrapped process finished. Exiting")

    exit(0)
