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
from spmi.utils.pattern import PatternMatcher, SimplePatternMatcher
from spmi.core.manageable import Manageable, ManageableException
from spmi.utils.exception import SpmiException
from spmi.utils.metadata import MetaDataError

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

VERSION = "SPMI 0.0.1 test"
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
        def task_id(self):
            """:obj:`str`: ID of task."""
            return self._args["<task_id>"]


    class ConfigHelper:
        """Manages SPMI configuration.

        Settings os SPMI are stored in environment variables:

        * ``SPMI_HOME`` is path to SPMI home directory.
        * ``SPMI_PATH`` is string of pathes splitted by ``:`` where SPMI tries to find descriptors.
        """

        DEFAULTS = {
            "SPMI_HOME": "/home/leonid/github.com/LeonidPilyugin/spmi/resources/test-spmi/",
            "SPMI_PATH": ".:/home/leonid/github.com/LeonidPilyugin/spmi/examples/task",
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

            assert "SPMI_HOME" in self._dict
            assert "SPMI_PATH" in self._dict

        def load(self):
            """Loads system environment variables."""
            for key in self._dict:
                self._dict[key] = os.environ.get(key, self._dict[key])

        @property
        def home(self):
            """:obj:`pathlib.Path`: Path to SPMI home directory."""
            return Path(self._dict["SPMI_HOME"])

        @property
        def path(self):
            """:obj:`list` of :obj:`pathlib.Path`: List of pathes."""
            return list(map(lambda x: Path(x).expanduser(), self._dict["SPMI_PATH"].split(":")))


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

        if not (self._config.home.is_dir() and self._config.home.exists()):
            self._logger.info(f"Creating directory \"{self._config.home}\"")
            self._config.home.mkdir(parents=True)

        self._logger.debug("Creating pool")
        self._pool = Pool(home=self._config.home, path = self._config.path, pm=pm)


    def show_list(self):
        """Prints list of manageables."""
        self._logger.debug("Listing manageables")
        
        for manageable in self._pool.detected:
            self._logger.info(f"Detected \"{manageable.state.id}\" of type \"{manageable.state.type}\" by path \"{manageable.state.data_path}\"")

        for manageable in self._pool.registered:
            with manageable:
                self._logger.info(f"Registered \"{manageable.state.id}\" of type \"{manageable.state.type}\"")

        self._logger.info(f"Detected {len(self._pool.detected)}")
        self._logger.info(f"Registered {len(self._pool.registered)}")

    def start(self, pattern):
        """Starts all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        self._logger.debug(f"Starting manageables by pattern \"{pattern}\"")

        to_start = self._pool.find(pattern, registered=False)
        started = 0
        
        if len(to_start) == 0:
            self._logger.warning("Nothing to start")
        else:
            for manageable in to_start:
                try:
                    self._logger.info(f"Starting manageable \"{manageable.state.id}\"")
                    self._pool.register(manageable)
                    with manageable:
                        manageable.start()
                    started += 1
                except (ManageableException, MetaDataError, PoolException) as e:
                    self._logger.warning(f"Failed to start \"{manageable.state.id}\": {e}")
                    if self._args.debug:
                        raise

        self._logger.info(f"Started {started} manageables")

    def restart(self, pattern):
        """Retarts all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        raise NotImplementedError()
        assert isinstance(pattern, str)

        self._logger.debug(f"Restarting manageables by pattern \"{pattern}\"")
        self._pool.restart(pattern)

    def stop(self, pattern):
        """Stops all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_stop = self._pool.find(pattern, detected=False)
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
                except (ManageableException, MetaDataError) as e:
                    self._logger.warning(f"Failed to stop \"{manageable.state.id}\": {e}")
                    if self._args.debug:
                        raise

        self._logger.info(f"Stopped {stopped} manageables")

    def kill(self, pattern):
        """Kills all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_kill = self._pool.find(pattern, detected=False)
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
                except (ManageableException, MetaDataError) as e:
                    self._logger.warning(f"Failed to kill \"{manageable.state.id}\": {e}")
                    if self._args.debug:
                        raise

        self._logger.info(f"Killed {killed} manageables")

    def status(self, pattern):
        """Prints status all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_show = self._pool.find(pattern, detected=False)

        if len(to_show) == 0:
            self._logger.warning("Nothing to show")
        else:
            for manageable in to_show:
                with manageable:
                    print(manageable.state)

        self._logger.info(f"Showed {len(to_show)} manageables")


    def clean(self, pattern):
        """Cleans all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        to_clean = self._pool.find(pattern, detected=False)
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
                except (ManageableException, MetaDataError) as e:
                    self._logger.warning(f"Failed to clean \"{manageable.state.id}\": {e}")
                    if self._args.debug:
                        raise

        self._logger.info(f"Cleaned {cleaned} manageables")

    def connect(self, task_id):
        """Prints stdout of task and prints to it stdin.

        Args:
            task_id (:obj:`str`): ID of task to connect.
        """
        tasks = self._pool.find(task_id, detected=False)
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
        elif self._args.is_start:
            for p in self._args.patterns: self.start(p)
        elif self._args.is_status:
            for p in self._args.patterns: self.status(p)
        elif self._args.is_stop:
            for p in self._args.patterns: self.stop(p)
        elif self._args.is_kill:
            for p in self._args.patterns: self.kill(p)
        elif self._args.is_clean:
            for p in self._args.patterns: self.clean(p)
        elif self._args.is_connect:
            self.connect(self._args.task_id)


if __name__ == "__main__":
    try:
        spmi = Spmi(docopt(HELP_MESSAGE, version=VERSION), SimplePatternMatcher())
        spmi.execute()
    except Exception as e:
        raise
