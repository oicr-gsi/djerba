"""
Abstract base class for helpers
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
from abc import ABC
from djerba.core.configurable import configurable
import djerba.core.constants as core_constants

class helper_base(configurable, ABC):

    def __init__(self, workspace, identifier, log_level=logging.INFO, log_path=None):
        # workspace is an instance of djerba.core.workspace
        super().__init__(identifier, log_level, log_path)
        self.workspace = workspace
        defaults = {
            core_constants.CONFIGURE_PRIORITY: self.DEFAULT_CONFIG_PRIORITY,
            core_constants.EXTRACT_PRIORITY: self.DEFAULT_CONFIG_PRIORITY,
        }
        self.set_all_ini_defaults(defaults)

    # configure() method is defined in parent class

    def extract(self, config_section):
        """
        Input is a config section from a ConfigParser object
        No output, but may write files to the shared workspace
        """
        msg = "Using placeholder method of parent class; does nothing"
        self.logger.debug(msg)
