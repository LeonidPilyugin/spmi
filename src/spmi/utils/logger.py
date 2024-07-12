"""Provides :class:`Logger`.
"""

import logging

class Logger:
    """Provides logging methods."""
    class DefaultFormatter(logging.Formatter):

        grey = "\x1b[38;20m"
        green = "\x1b[32;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: green + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    @staticmethod
    def basic_config(loglevel="INFO"):
        """Sets up logging basic config.

        Args:
            loglevel: :py:mod:`logging` log level.
        """
        logging.basicConfig(level=loglevel)

    @staticmethod
    def log_level():
        """Returns global log level."""
        return logging.root.level

    def __init__(self, name):
        """
        Args:
            name (:obj:`str`): Logger name.
        """
        self._logger = logging.getLogger(name)
        self._logger.handlers.clear()
        ch = logging.StreamHandler()
        ch.setFormatter(Logger.DefaultFormatter())
        self._logger.addHandler(ch)
        self._logger.propagate = False

    def debug(self, msg):
        """Debug a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self._logger.debug(msg)

    def info(self, msg):
        """Info a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self._logger.info(msg)

    def warning(self, msg):
        """Warning a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self._logger.warning(msg)

    def error(self, msg):
        """Error a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self._logger.error(msg)

    def critical(self, msg):
        """Critical a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self._logger.critical(msg)
