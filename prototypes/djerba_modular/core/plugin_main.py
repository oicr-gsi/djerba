"""Base class for plugin API"""

import logging
from djerba.util.logger import logger

class main(logger):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    # methods to be implemented by subclasses

    def configure(self, ini_path, work_dir):
        # returns a dictionary representing the INI section for the plugin
        msg = "configure() method of base class not intended for production; define a subclass instead"
        self.logger.error(msg)
        raise RuntimeError(msg)

    def extract(self, ini_path, work_dir):
        # returns JSON
        msg = "extract() method of base class not intended for production; define a subclass instead"
        self.logger.error(msg)
        raise RuntimeError(msg)

    def render(self, json_path, work_dir):
        # returns HTML
        msg = "render() method of base class not intended for production; define a subclass instead"
        self.logger.error(msg)
        raise RuntimeError(msg)

