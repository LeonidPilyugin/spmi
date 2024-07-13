#!/usr/bin/env python3

"""SPMI application module.

Execute next command to get help message:

.. code-block:: console

    $ spmi --help


Todo:
    * Exceptions
    * Error handling
"""

import os
import sys
import traceback
from typing import List
from pathlib import Path
from docopt import docopt
from spmi.core.pool import Pool, PoolException
from spmi.utils.logger import Logger
from spmi.utils.io.io import Io
from spmi.utils.pattern import PatternMatcher, RegexPatternMatcher
from spmi.core.manageable import Manageable, ManageableException
from spmi.utils.exception import SpmiException
from spmi.utils.metadata import MetaDataError
from spmi.utils.exception import SpmiException

HELP_MESSAGE = r"""
   _____ ____  __  _______
  / ___// __ \/  |/  /  _/
  \__ \/ /_/ / /|_/ // /
 ___/ / ____/ /  / // /
/____/_/   /_/  /_/___/

Simple Process Management Interface

SPMI is a program to maintain processes.

Usage:
    spmi list [-d | --debug]
    spmi register <pathes>... [-d | --debug]
    spmi start <patterns>... [-d | --debug]
    spmi stop <patterns>... [-d | --debug]
    spmi kill <patterns>... [-d | --debug]
    spmi clean <patterns>... [-d | --debug]
    spmi status <patterns>... [-d | --debug]
    spmi connect <task_id> [-d | --debug]

Options:
    -h --help       Show this screen
    -v --version    Show version
    -d --debug      Run in debug mode

"""

VERSION = "SPMI 0.0.1"
"""str: Version of SPMI"""

class Spmi:
    """Main aplication class.

    Provides methods to start application.
    """
    class ArgumentsHelper:
        """Command line argument container.

        Provides methods to work with ``docopt`` arguments
        """

        def __init__(self, args):
            """
            Args:
                args (:obj:`dict`): Dictionary, returned by ``docopt.docopt``.
            """
            assert isinstance(args, dict)
            self._args = args

        @property
        def is_register(self):
            """:obj:`bool`: ``True`` if should register."""
            return self._args["register"]

        @property
        def is_start(self):
            """:obj:`bool`: ``True``, if should start."""
            return self._args["start"]

        @property
        def is_stop(self):
            """:obj:`bool`: ``True``, if should stop."""
            return self._args["stop"]

        @property
        def is_kill(self):
            """:obj:`bool`: ``True``, if should kill."""
            return self._args["kill"]

        @property
        def is_clean(self):
            """:obj:`bool`: ``True``, if should clean."""
            return self._args["clean"]

        @property
        def is_status(self):
            """:obj:`bool`: ``True``, if should show status."""
            return self._args["status"]

        @property
        def is_list(self):
            """:obj:`bool`: ``True``, if should show list."""
            return self._args["list"]

        @property
        def is_connect(self):
            """:obj:`bool`: ``True``, if should connect to task."""
            return self._args["connect"]

        @property
        def debug(self):
            """:obj:`bool`: ``True`` if ``--debug`` in options."""
            return self._args["--debug"]

        @property
        def patterns(self):
            """:obj:`list` of :obj:`str`: List of patterns."""
            return self._args["<patterns>"]

        @property
        def pathes(self):
            """:obj:`list` of :obj:`str`: List of pathes."""
            return [Path(x).expanduser() for x in self._args["<pathes>"]]

        @property
        def task_id(self):
            """:obj:`str`: ID of task."""
            return self._args["<task_id>"]


    class ConfigHelper:
        """Manages SPMI configuration.

        Settings os SPMI are stored in environment variables:

        * ``SPMI_PATH`` is path to SPMI home directory.
        """

        DEFAULTS = {
            "SPMI_PATH": "~/.spmi",
        }
        """:obj:`dict` Default SPMI settings."""

        def __init__(self, defaults = None):
            """
            Args:
                defaults (:obj:`Union[dict, None]`): default settings.
                    If None, defaults are set from ``DEFAULTS`` attribute.
            """
            assert defaults is None or isinstance(defaults, dict)
            self._dict = defaults if not defaults is None else dict(Spmi.ConfigHelper.DEFAULTS)
            self.load()

            assert "SPMI_PATH" in self._dict

        def _check(self):
            try:
                path = Path(self._dict["SPMI_PATH"]).expanduser()
                if path.exists() and not path.is_dir():
                    raise SpmiException(f"Path \"{path}\" must be a directory")
            except Exception as e:
                raise SpmiException(f"Invalid \"SPMI_PATH\" variable:\n{e}") from e

        def load(self):
            """Loads system environment variables.

            Raises:
                :class:`SpmiException`
            """
            for key in self._dict:
                self._dict[key] = os.environ.get(key, self._dict[key])
            self._check()

        @property
        def path(self):
            """:obj:`pathlib.Path`: Path to SPMI home directory."""
            return Path(self._dict["SPMI_PATH"]).expanduser()


    def __init__(self, args, pm):
        """
        Args:
            args (:obj:`dict`): ``docopt`` arguments.
            pm (:obj:`spmi.utils.pattern.PatternMatcher`): Pattern matcher.
        """
        assert isinstance(pm, PatternMatcher)
        assert isinstance(args, dict)

        self._logger = Logger("Spmi")
        self._logger.debug("Loading arguments")
        self._args = Spmi.ArgumentsHelper(args)

        Logger.basic_config(loglevel="DEBUG" if self._args.debug else "INFO")

        self._logger.debug("Loading config")
        self._config = Spmi.ConfigHelper()

        if not (self._config.path.is_dir() and self._config.path.exists()):
            self._logger.info(f"Creating directory \"{self._config.home}\"")
            self._config.home.mkdir(parents=True)

        self._logger.debug("Creating pool")
        self._pool = Pool(path=self._config.path, pm=pm)

    def register(self, pathes):
        registered = 0
        try:
            to_register = []

            for path in pathes:
                to_register.append(Manageable.from_descriptor(path))

            for m in to_register:
                self._pool.register(m)
                registered += 1
        except SpmiException as e:
            self._logger.error(f"Failed to register:\n{e}")
            if self._args.debug:
                raise
        finally:
            self._logger.info(f"Registered {registered} manageable{'' if registered == 1 else 's'}")


    def show_list(self):
        """Prints list of manageables."""
        self._logger.debug("Listing manageables")

        states = []
        
        for manageable in self._pool.manageables:
            with manageable:
                states.append((manageable.state, "active" if manageable.active else "inactive"))

        self._logger.info(f"Registered {len(self._pool.manageables)} manageable{'' if len(self._pool.manageables) == 1 else 's'}")

        max_id_len = 1 if not states else max(map(lambda x: len(x[0].id), states)) + 1
        max_id_len = max(max_id_len, 10)

        max_active_len = 1 if not states else max(map(lambda x: len(x[1]), states)) + 1
        max_active_len = max(max_active_len, 10)

        max_comment_len = 1 if not states else max(map(lambda x: len(x[0].comment), states)) + 1
        max_comment_len = max(max_comment_len, 10)

        print(f"{{:{max_id_len}}}{{:<{max_active_len}}}{{:<{max_comment_len}}}".format("ID", "ACTIVE", "COMMENT"))
        for s in states:
            print(f"{{:<{max_id_len}}}{{:<{max_active_len}}}{{:<{max_comment_len}}}".format(s[0].id, s[1], s[0].comment))

    def start(self, patterns):
        """Starts all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_start = []
        for pattern in patterns:
            to_start.extend(self._pool.find(pattern))
        started = 0
        
        if len(to_start) == 0:
            self._logger.warning("Nothing to start")
        else:
            for manageable in to_start:
                try:
                    self._logger.info(f"Starting manageable \"{manageable.state.id}\"")
                    with manageable:
                        manageable.start()
                    started += 1
                except SpmiException as e:
                    self._logger.error(f"Failed to start \"{manageable.state.id}\":\n{e}")
                    if self._args.debug:
                        raise

        self._logger.info(f"Started {started} manageables")

    def stop(self, patterns):
        """Stops all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_stop = []
        for pattern in patterns:
            to_stop.extend(self._pool.find(pattern))
        stopped = 0

        if len(to_stop) == 0:
            self._logger.warning("Nothing to stop")
        else:
            for manageable in to_stop:
                try:
                    self._logger.info(f"Stopping manageable \"{manageable.state.id}\"")
                    with manageable:
                        manageable.term()
                    stopped += 1
                except SpmiException as e:
                    self._logger.error(f"Failed to stop \"{manageable.state.id}\":\n{e}")
                    if self._args.debug:
                        raise

        self._logger.info(f"Stopped {stopped} manageables")

    def kill(self, patterns):
        """Kills all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_kill = []
        for pattern in patterns:
            to_kill.extend(self._pool.find(pattern))
        killed = 0

        if len(to_kill) == 0:
            self._logger.warning("Nothing to kill")
        else:
            for manageable in to_kill:
                try:
                    self._logger.info(f"Killing manageable \"{manageable.state.id}\"")
                    with manageable:
                        manageable.kill()
                    killed += 1
                except SpmiException as e:
                    self._logger.error(f"Failed to kill \"{manageable.state.id}\":\n{e}")
                    if self._args.debug:
                        raise

        self._logger.info(f"Killed {killed} manageables")

    def status(self, patterns):
        """Prints status all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_show = []
        for pattern in patterns:
            to_show.extend(self._pool.find(pattern))

        if len(to_show) == 0:
            self._logger.warning("Nothing to show")
        else:
            for manageable in to_show:
                with manageable:
                    print(manageable.status_string())

        self._logger.info(f"Showed {len(to_show)} manageables")


    def clean(self, patterns):
        """Cleans all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_clean = []
        for pattern in patterns:
            to_clean.extend(self._pool.find(pattern))
        cleaned = 0

        if len(to_clean) == 0:
            self._logger.warning("Nothing to clean")
        else:
            for manageable in to_clean:
                try:
                    self._logger.info(f"Cleaning manageable \"{manageable.state.id}\"")
                    with manageable:
                        manageable.destruct()
                    cleaned += 1
                except SpmiException as e:
                    self._logger.error(f"Failed to clean \"{manageable.state.id}\":\n{e}")
                    if self._args.debug:
                        raise

        self._logger.info(f"Cleaned {cleaned} manageables")

    def connect(self, task_id):
        """Prints stdout of task and prints to it stdin.

        Args:
            task_id (:obj:`str`): ID of task to connect.
        """
        tasks = self._pool.find(task_id)
        assert len(tasks) == 1
        task = tasks[0]

        with task:
            stdout_path = task.state.wrapper.stdout_path

            assert stdout_path and stdout_path.exists()

            with open(stdout_path) as f:
                print(f.read(), end="")

            stdin_path = task.state.wrapper.stdin_path
            if stdin_path and stdin_path.exists():
                with open(stdin_path, "w") as pipe:
                    pipe.write(input() + "\n")

    def execute(self):
        """Execute command from CLI."""

        if self._args.is_list:
            self.show_list()
        elif self._args.is_register:
            self.register(self._args.pathes)
        elif self._args.is_start:
            self.start(self._args.patterns)
        elif self._args.is_status:
            self.status(self._args.patterns)
        elif self._args.is_stop:
            self.stop(self._args.patterns)
        elif self._args.is_kill:
            self.kill(self._args.patterns)
        elif self._args.is_clean:
            self.clean(self._args.patterns)
        elif self._args.is_connect:
            self.connect(self._args.task_id)


if __name__ == "__main__":
    try:
        spmi = Spmi(docopt(HELP_MESSAGE, version=VERSION), RegexPatternMatcher())
        spmi.execute()
    except Exception as e:
        raise
