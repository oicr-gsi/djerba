"""
Abstract base class for helpers
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
from abc import ABC
from djerba.core.configure import configurable
import djerba.core.constants as core_constants

class helper_base(configurable, ABC):

    PRIORITY_KEYS = [
        core_constants.CONFIGURE_PRIORITY,
        core_constants.EXTRACT_PRIORITY
    ]

    def __init__(self, **kwargs):
        # workspace is an instance of djerba.core.workspace
        super().__init__(**kwargs)
        self.workspace = kwargs['workspace']
        defaults = {k: self.DEFAULT_PRIORITY for k in self.PRIORITY_KEYS}
        self.set_all_ini_defaults(defaults)
        self.specify_params()

    # configure() method is defined in parent class

    def extract(self, config_section):
        """
        Input is a config section from a ConfigParser object
        No output, but may write files to the shared workspace
        """
        msg = "Using placeholder method of parent class; does nothing"
        self.logger.debug(msg)
