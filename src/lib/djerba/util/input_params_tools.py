"""
Tools for checking and importing input_params.json
"""

# IMPORTS
import os
import logging
from djerba.util.logger import logger
from djerba.plugins.base import plugin_base
from djerba.core.workspace import workspace


def get_input_params_json(self):
    """
    Checks if input_params.json exists
    If it does, it reads it
    """
    input_params_file = "input_params.json"

    # If input_params.json exists, read it
    if self.workspace.has_file(input_params_file): 
        input_data = self.workspace.read_json(input_params_file)
        msg = "Found and using parameters from input_params.json."
        self.logger.debug(msg)
        return input_data
    
    # Otherwise, log a warning that says that it could not find input_params.json
    # and that parameters must be manually inputted
    else:
        msg = "Could not find input_params.json. Parameters must be manually supplied."
        self.logger.debug(msg)

