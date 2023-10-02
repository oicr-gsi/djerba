"""
Base class for merger factories.
A factory can be used by a plugin to generate correctly formatted JSON for a merger.
"""

import logging
from abc import ABC
from djerba.util.logger import logger

class factory(logger, ABC):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, log_path)

    def get_json(**kwargs):
        """
        Child classes will map from kwargs to a dictionary with appropriate keys
        """
        pass
        
        
