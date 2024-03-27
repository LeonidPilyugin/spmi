import argparse
import pathlib
from collections import namedtuple
import enum
import toml
from pathlib import Path
from .utils.logger import Logger

class Pls:
    """
    Main program class
    """
    
    class Config:
        """
        Config class
        """
        DEFAULTS = {
            "pool": {
                "directory": "/home/leonid/github.com/LeonidPilyugin/pls/resources/.sls",
                "pool": "default",
            },
        }

        def __init__(self, file: Path):
            self.file = file
            self.dict = dict(Pls.Config.DEFAULTS)

        def load(self):
            """
            Loads settings from config file
            """
            if not self.file.exists():
                return

            with open(self.file, "w") as f:
                config = toml.load(f)

            def recursive_copy(src: dict, dst: dict):
                for key, value in src.items():
                    if isinstance(src[key], dict):
                        recursive_copy(src[key], dst[key])
                    else:
                        dst[key] = src[key]

            recursive_copy(config, self.dict)

        def __getitem__(self, key):
            return self.dict[key]

        def __setitem__(self, key, value):
            self.dict[key] = value

        def __delitem__(self, key):
            del self.dict[key]


    class ArgParser:
        """
        CLI arg parser
        """
        Option = namedtuple("Option", "type help handler")

        def __init__(self, options: dict):
            self.parser = argparse.ArgumentParser(
                prog="Process Launching System",
                description="Launch your processes in different process managers with single interface",
            )

            self.options = options

            for option, add in options.items():
                self.parser.add_argument(f"--{option}", type=add.type, help=add.help)

        def parse(self):
            args = self.parser.parse_args
            
            for option, arg in vars(args).items():
                if arg is None:
                    self.options[option].handler()
                else:
                    self.options[option].handler(arg)

    
    CONFIG_PATH = "/home/leonid/github.com/LeonidPilyugin/pls/resources/.slsrc"

    def __init__(self):
        self.config = Config(Pls.CONFIG_PATH)
        self.argparser = Pls.ArgParser(
            options = {
                "start": Pls.ArgParser.Option(str, "Start task by descriptor", self.on_start),
                "stop": Pls.ArgParser.Option(str, "Stop task by id", self.on_stop),
                "status": Pls.ArgParser.Option(str, "Get status of task by id", self.on_status),
                "remove": Pls.ArgParser.Option(str, "Remove task by id", self.on_remove),
                "list": Pls.ArgParser.Option(None, "Get list of tasks", self.on_list),
                "loglevel": Pls.ArgParser.Option(str, "Set log level", self.on_loglevel),
            }
        )


    def load_pool(self):
        self.pool = load_pool(self.config["Pool"], Path(self.config["directory"]))


    def start(self):
        self.argparser.parse()

    def on_start(self, descriptor: str):
        task = self.pool.create_task(Path(descriptor))
        task.start()

    def on_stop(self, task_id: str):
        task = filter(lambda task: task.descriptor["id"] == task_id, self.pool.tasks)[0]
        task.stop()

    def on_status(self, task_id: str):
        task = filter(lambda task: task.descriptor["id"] == task_id, self.pool.tasks)[0]
        print(task.descriptor.dict)

    def on_remove(self, task_id: str):
        self.pool.remove_task(task_id)

    def on_list(self):
        print(self.pool.tasks)

    def on_loglevel(self, level):
        Logger.set_loglevel(level)


if __name__ == "__main__":
    logger = Logger("Main")
    logger.debug("Started")

    pls = Pls()
    pls.start()

