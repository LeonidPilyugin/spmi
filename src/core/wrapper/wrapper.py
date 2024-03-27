class Wrapper(metaclass=ABCMeta):
    """
    A wrapper for running process. Handles signals and output.
    """

    class Command:
        """
        Describes a command line args passed to wrapper script
        """
        WRAPPER_FILE_ARG = "--pls-wrapper-file"
        LOG_FILE_ARG = "--pls-log-file"
        COMMAND_ARG = "--pls-command"

        def __init__(
            self,
            wrapper_file: str,
            log_file: str,
            command: str
        ):
            self.wrapper_file = wrapper_file
            self.log_file = log_file,
            self.command = command

        @classmethod
        def from_string(string: str):
            """
            Generates a command from string
            """
            command = string.split(COMMAND_ARG)[1].trunc()
            pls_args = string.split(COMMAND_ARG)[0].trunc()

            parser = argparse.ArgumentParser()
            parser.add_argument(Cover.Command.WRAPPER_FILE_ARG, type=str)
            parser.add_argument(Cover.Command.LOG_FILE_ARG, type=str)

            args = parser.parse_args(string.split())

            return Cover.Command(
                parser[Cover.Command.WRAPPER_FILE_ARG],
                parser[Cover.Command.LOG_FILE_ARG],
                command
            )


        def __str__(self):
            return (
                f"{Cover.Command.WRAPPER_FILE_ARG} {self.frapper_file} "
                f"{Cover.Command.LOG_FILE_ARG} {self.log_file} "
                f"{Cover.Command.COMMAND_ARG} {self.command}"
            )
    
    @abstractmethod
    def on_term(self):
        """
        Handles SIGTERM and SIGINT
        """
        pass

    @abstractmethod
    def run(self):
        """
        Starts a wrapped process
        """
        pass




def load_wrapper(wrapper: str) -> Wrapper:
    pass
