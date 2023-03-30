"""
Abstract base class for mergers
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
from abc import ABC
from djerba.util.logger import logger

class merger_base(logger, ABC):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.debug("Using constructor of parent class")

    def render(self, inputs):
        """
        Input is a list of data structures, obtained one or more plugins
        Each input structure must match the schema for this merger
        Output is a string (for inclusion in an HTML document)
        """
        msg = "Using method of parent class; checks inputs and returns empty string"
        self.logger.debug(msg)
        self.json_validator.validate_data(data)
        return ''
