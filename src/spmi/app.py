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
from spmi.core.pool import Pool
from spmi.utils.logger import Logger
from spmi.utils.io.io import Io
from spmi.utils.pattern import PatternMatcher, SimplePatternMatcher
from spmi.core.manageable import Manageable

HELP_MESSAGE = r"""
   _____ ____  __  _______
  / ___// __ \/  |/  /  _/
  \__ \/ /_/ / /|_/ // /
 ___/ / ____/ /  / // /
/____/_/   /_/  /_/___/

Simple Process Management Interface

SPMI is a program to maintain processes with systemctl-like interface.

Usage:
    spmi list [-d | --debug]
    spmi start <patterns>... [-d | --debug]
    spmi stop <patterns>... [-d | --debug]
    spmi clean <patterns>... [-d | --debug]
    spmi status <patterns>... [-d | --debug]

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
        def debug(self):
            """:obj:`bool`: ``True`` if ``--debug`` in options."""
            return self._args["--debug"]

        @property
        def patterns(self):
            """:obj:`list` of :obj:`str`: List of patterns."""
            return self._args["<patterns>"]


    class ConfigHelper:
        """Manages SPMI configuration.

        Settings os SPMI are stored in environment variables:

        * ``SPMI_HOME`` is path to SPMI home directory.
        * ``SPMI_PATH`` is string of pathes splitted by ``:`` where SPMI tries to find descriptors.
        """

        DEFAULTS = {
            "SPMI_HOME": "/home/leonid/github.com/LeonidPilyugin/spmi/resources/test-spmi/",
            "SPMI_PATH": ".:/home/leonid/github.com/LeonidPilyugin/spmi/examples/tasks",
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
            return list(map(Path, self._dict["SPMI_PATH"].split(":")))


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
        self._pool = Pool(path=self._config.home, pm=pm, dm=self.load_manageables())


    def load_manageables(self):
        """Return list of found descriptors.
        
        Returns:
            :obj:`list` of :obj:`spmi.manageable.Manageable`:
            :obj:`list` of detected manageables.
        """

        manageables = []
        self._logger.debug("Loading manageables")

        for root in self._config.path:
            self._logger.debug(f"Loading from \"{root}\"")
            for path_object in root.rglob("*"):
                if path_object.is_file() and Io.has_io(path_object):
                    self._logger.debug(f"Trying to load \"{path_object}\"")

                    try:
                        new_manageable = Manageable.from_descriptor(path_object)
                    except Exception as e:
                        self._logger.warning(
                            f"Cannot load descriptor \"{path_object}\": {traceback.format_exc(e)}"
                        )
                        continue

                    manageables.append(new_manageable)

        self._logger.debug(f"Loaded {len(manageables)} detected manageables")

        return manageables

    def show_list(self):
        """Prints list of manageables."""
        self._logger.debug("Listing manageables")
        print(self._pool.get_list_string())

    def start(self, pattern: str):
        """Starts all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        assert isinstance(pattern, str)

        self._logger.debug(f"Starting manageables by pattern \"{pattern}\"")
        self._pool.start(pattern)

    def restart(self, pattern):
        """Retarts all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        assert isinstance(pattern, str)

        self._logger.debug(f"Restarting manageables by pattern \"{pattern}\"")
        self._pool.restart(pattern)

    def stop(self, pattern):
        """Starts all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        assert isinstance(pattern, str)

        self._logger.debug(f"Stopping manageables by pattern \"{pattern}\"")
        self._pool.stop(pattern)

    def status(self, pattern):
        """Starts all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        assert isinstance(pattern, str)

        self._logger.debug(f"Printing status of manageables by pattern \"{pattern}\"")
        print(self._pool.get_status_string(pattern))

    def clean(self, pattern):
        """Starts all manageables corresponding to pattern.

        Args:
            pattern (:obj:`str`): Pattern string.
        """
        assert isinstance(pattern, str)

        self._logger.debug(f"Cleaning manageables by pattern \"{pattern}\"")
        self._pool.destruct(pattern)

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
        elif self._args.is_clean:
            for p in self._args.patterns: self.clean(p)


if __name__ == "__main__":
    try:
        spmi = Spmi(docopt(HELP_MESSAGE, version=VERSION), SimplePatternMatcher())
        spmi.execute()
    except Exception as e:
        print(f"Unknown error: {traceback.format_exc(e)}")
        sys.exit(1)
