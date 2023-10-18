"""Archive files to couchDB for later reference"""

import hashlib
import json
import logging
import os
import re

import djerba.util.constants as constants
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.validator import path_validator
from djerba.core.database.database import database

class archiver(logger):
    """Archive the report JSON to couchDB"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.converter = converter(log_level, log_path)
        self.validator = path_validator(log_level, log_path)

    def run(self, data):
        uploaded, report_id = database(self.log_level, self.log_path).upload_data(data)
        return uploaded, report_id
