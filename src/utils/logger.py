import logging

class Logger:
    """
    Logger class
    """

    @classmethod
    def basic_config(loglevel="WARNING"):
        logging.basicConfig(level=loglevel)
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)
