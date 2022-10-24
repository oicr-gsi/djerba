"""Archive files to couchDB for later reference"""

import hashlib
import json
import logging
import shutil
import os
import re

import djerba.util.constants as constants
import djerba.render.constants as render_constants
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.validator import path_validator
from djerba.render.database import Database 


class archiver(logger):
    """Archive the report JSON to a directory, with hashing to avoid overwrites"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.converter = converter(log_level, log_path)
        self.validator = path_validator(log_level, log_path)
        self.logger.info('Initializing archiver object from archiver.py')

    def read_and_preprocess(self, data_path):
        # read the JSON and convert image paths to base64 blobs
        self.logger.debug("Reading data path {0}".format(data_path))
        with open(data_path) as data_file:
            data_string = data_file.read()
        data = json.loads(data_string)
        # shorter key names
        rep = constants.REPORT
        tmb = render_constants.TMB_PLOT
        vaf = render_constants.VAF_PLOT
        logo = render_constants.OICR_LOGO
        # convert image paths (if any, they may already be base64)
        data[rep][logo] = self.converter.convert_png(data[rep][logo], 'OICR logo')
        data[rep][tmb] = self.converter.convert_svg(data[rep][tmb], 'TMB plot')
        data[rep][vaf] = self.converter.convert_svg(data[rep][vaf], 'VAF plot')
        return json.dumps(data)

    def db(self, data_path):
        self.logger.info('run method from archiver class STARTING')
        data_string = self.read_and_preprocess(data_path)
        status = Database().UploadFile(data_path) ###data_path is path to json file      
        return status

