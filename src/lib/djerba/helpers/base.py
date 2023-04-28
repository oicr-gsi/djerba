"""
Abstract base class for helpers
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
from abc import ABC
from djerba.core.component import component

class helper_base(component, ABC):

    def __init__(self, workspace, log_level=logging.INFO, log_path=None):
        # workspace is an instance of djerba.core.workspace
        self.workspace = workspace
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.debug("Using constructor of parent class")

    def configure(self, config_section):
        """Input/output is a config section from a ConfigParser object"""
        self.logger.debug("Using method of parent class; returns unchanged config")
        return config_section

    def extract(self, config_section):
        """
        Input is a config section from a ConfigParser object
        No output, but may write files to the shared workspace
        """
        msg = "Using placeholder method of parent class; does nothing"
        self.logger.debug(msg)
