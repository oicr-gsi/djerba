"""
Abstract base class for helpers
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
from abc import ABC, abstractmethod
from djerba.core.configure import configurable
import djerba.core.constants as core_constants

class helper_base(configurable, ABC):

    PRIORITY_KEYS = [
        core_constants.CONFIGURE_PRIORITY,
        core_constants.EXTRACT_PRIORITY
    ]   # render priority is not defined for helpers

    def __init__(self, **kwargs):
        # workspace is an instance of djerba.core.workspace
        super().__init__(**kwargs)
        self.workspace = kwargs['workspace']
        # global defaults for helpers; can override for individual helper classes
        self.ini_defaults = {
            core_constants.ATTRIBUTES: '',
            core_constants.DEPENDS_CONFIGURE: '',
            core_constants.DEPENDS_EXTRACT: '',
            core_constants.CONFIGURE_PRIORITY: 1000,
            core_constants.EXTRACT_PRIORITY: 1000,
        }
        self.specify_params()

    # configure() method is defined in parent class

    @abstractmethod
    def extract(self, config_section):
        """
        Input is a config section from a ConfigParser object
        No output, but may write files to the shared workspace
        """
        msg = "Using placeholder method of parent class; does nothing"
        self.logger.debug(msg)

    def set_priority_defaults(self, priority):
        for key in self.PRIORITY_KEYS:
            self.ini_defaults[key] = priority
