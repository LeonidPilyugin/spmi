"""Provides :class:`Logger`.
"""

import logging

class Logger:
    """Provides logging methods."""

    @staticmethod
    def basic_config(loglevel="INFO"):
        """Sets up logging basic config.

        Args:
            loglevel: :py:mod:`logging` log level.
        """
        logging.basicConfig(level=loglevel)

    def __init__(self, name):
        """
        Args:
            name (:obj:`str`): Logger name.
        """
        self.logger = logging.getLogger(name)

    def debug(self, msg):
        """Debug a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self.logger.debug(msg)

    def info(self, msg):
        """Info a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self.logger.info(msg)

    def warning(self, msg):
        """Warning a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self.logger.warning(msg)

    def error(self, msg):
        """Error a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self.logger.error(msg)

    def critical(self, msg):
        """Critical a message.

        Args:
            msg (:obj:`str`): message to show.
        """
        self.logger.critical(msg)
