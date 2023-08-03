"""Archive files to couchDB for later reference"""

import hashlib
import json
import logging
import os
import re

import djerba.util.constants as constants
import djerba.render.constants as render_constants
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.validator import path_validator
from djerba.core.database.database import database

class archiver(logger):
    """Archive the report JSON to a directory, with hashing to avoid overwrites"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.converter = converter(log_level, log_path)
        self.validator = path_validator(log_level, log_path)

    def preprocess_for_upload(self, data):
        # shorter key names
        failed = render_constants.FAILED
        rep = constants.REPORT
        vaf = render_constants.VAF_PLOT
        cnv = render_constants.CNV_PLOT
        logo = render_constants.OICR_LOGO
        # convert image paths (if any, they may already be base64)
        data[rep][logo] = self.converter.convert_png(data[rep][logo], 'OICR logo')
        if not data[rep][failed]:
            for key in [ vaf, cnv]:
                data[rep][key] = self.converter.convert_svg(data[rep][key], key)
        return json.dumps(data)

    def run(self, data):
        data = self.preprocess_for_upload(data)
        uploaded, report_id = database(self.log_level, self.log_path).upload_data(data)
        return uploaded, report_id
