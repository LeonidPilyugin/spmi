"""
.. module:: logger.py
    :platform: Unix

.. moduleauthor:: Leonid Pilyugin <l.pilyugin04@gmail.com>

"""


import logging

class Logger:
    """Logger class."""

    @staticmethod
    def basic_config(loglevel="WARNING"):
        """Sets up logging basic config.

        Args:
            loglevel: log level.
        """
        logging.basicConfig(level=loglevel)

    def __init__(self, name: str):
        """Constructor.

        Args:
            name (str): logger name.
        """
        self.logger = logging.getLogger(name)

    def debug(self, msg: str):
        """Debug a message.

        Args:
            msg (str): messae to show.
        """
        self.logger.debug(msg)

    def info(self, msg: str):
        """Info a message.

        Args:
            msg (str): messae to show.
        """
        self.logger.info(msg)

    def warning(self, msg: str):
        """Warning a message.

        Args:
            msg (str): messae to show.
        """
        self.logger.warning(msg)

    def error(self, msg: str):
        """Error a message.

        Args:
            msg (str): messae to show.
        """
        self.logger.error(msg)

    def critical(self, msg: str):
        """Critical a message.

        Args:
            msg (str): messae to show.
        """
        self.logger.critical(msg)
