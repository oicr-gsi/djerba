"""
Tools for checking and importing input_params.json
"""

# IMPORTS
import os
import logging
from djerba.util.logger import logger
from djerba.plugins.base import plugin_base
from djerba.core.workspace import workspace


def get_input_params_json(workspace):
    """
    Checks if input_params.json exists
    If it does, it reads it
    """
    input_params_file = "input_params.json"

    # Get the working directory
    work_dir = workspace.get_work_dir()

    # Get input params path
    input_data_path = os.path.join(work_dir, input_params_file)

    # If input_params.json exists, read it
    if os.path.exists(input_data_path):
        input_data = workspace.read_json(input_params_file)
        return input_data
    
    # Otherwise, log a warning that says that it could not find input_params.json
    # and that parameters must be manually inputted
    else:
        msg = "Could not find input_params.json. Parameters must be manually supplied."
        print(msg)
        #print(msg) <-- TO DO: have logger raise warning

