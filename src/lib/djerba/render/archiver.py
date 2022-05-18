"""Archive files to a given directory for later reference"""

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

class archiver(logger):
    """Archive the report JSON to a directory, with hashing to avoid overwrites"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.converter = converter(log_level, log_path)
        self.validator = path_validator(log_level, log_path)

    def read_and_preprocess(self, data_path):
        # read the JSON and convert image paths to base64 blobs
        self.logger.debug("Reading data path {0}".format(data_path))
        with open(data_path) as data_file:
            data_string = data_file.read()
        data = json.loads(data_string)
        # shorter key names
        report = constants.REPORT
        tmb_key = render_constants.TMB_PLOT
        vaf_key = render_constants.VAF_PLOT
        logo_key = render_constants.OICR_LOGO
        # convert image paths (if any, they may already be base64)
        if self.converter.is_convertible(data[report][logo_key], 'OICR logo'):
            data[report][logo_key] = self.converter.convert_png(data[report][logo_key])
        if self.converter.is_convertible(data[report][tmb_key], 'TMB plot'):
            data[report][tmb_key] = self.converter.convert_jpeg(data[report][tmb_key])
        if self.converter.is_convertible(data[report][vaf_key], 'VAF plot'):
            data[report][vaf_key] = self.converter.convert_jpeg(data[report][vaf_key])
        return json.dumps(data)

    def run(self, data_path, archive_dir, patient_id):
        data_string = self.read_and_preprocess(data_path)
        m = hashlib.md5()
        m.update(data_string.encode(constants.TEXT_ENCODING))
        md5sum = m.hexdigest()
        # construct the output path, creating directories if necessary
        self.validator.validate_output_dir(archive_dir)
        archive_dir = os.path.realpath(archive_dir)
        out_dir_0 = os.path.join(archive_dir, patient_id)
        if not os.path.exists(out_dir_0):
            os.mkdir(out_dir_0)
        out_dir_1 = os.path.join(out_dir_0, md5sum)
        out_path = None
        # if output was not previously written, write it now
        if not os.path.exists(out_dir_1):
            os.mkdir(out_dir_1)
        suffix = md5sum[0:8]
        out_path = os.path.join(out_dir_1, "{0}_{1}.json".format(patient_id, suffix))
        if os.path.exists(out_path):
            msg = "Output path {0} exists; ".format(out_path)+\
                  "an identical file has already been archived; not writing to archive"
            self.logger.debug(msg)
        else:
            with open(out_path, 'w') as out_file:
                out_file.write(data_string)
            self.logger.debug("Archived JSON to {0}".format(out_path))
        return out_path
