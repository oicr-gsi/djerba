"""Archive files to a given directory for later reference"""

import hashlib
import json
import logging
import os

import djerba.util.constants as constants
import djerba.render.constants as render_constants
from djerba.util.image_to_base64 import convert_jpeg
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class archiver(logger):
    """Archive the report JSON to a directory, with hashing to avoid overwrites"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)

    def convert(self, in_path):
        if os.access(tmb_path, os.R_OK):
            converted = convert_jpeg(in_path)
            self.logger.debug("Converted plot {0} to base64 string".format(in_path))
        else:
            self.logger.debug("Cannot read {0}, omitting base64 conversion".format(in_path))
            converted = None
        return converted

    def read_and_preprocess(self, data_path):
        # read the JSON and convert image paths to base64 blobs
        with open(data_path) as data_file:
            self.data_string = data_file.read()
        data = json.loads(data_string)
        report = constants.REPORT
        tmb_converted = self.convert(data[constants.REPORT][render_constants.TMB_PLOT])
        if tmb_converted:
            data[constants.REPORT][render_constants.TMB_PLOT] = tmb_converted
        vaf_converted = self.convert(data[constants.REPORT][render_constants.VAF_PLOT])
        if vaf_converted:
            data[constants.REPORT][render_constants.VAF_PLOT] = vaf_converted
        return json.dumps(data)

    def run(self, data_path, archive_dir, patient_id):
        data_string = self.read_and_preprocess(data_path)
        m = hashlib.md5()
        m.update(self.data_string.encode(constants.TEXT_ENCODING))
        md5sum = m.hexdigest()
        # construct the output path, creating directories if necessary
        path_validator().validate_output_dir(archive_dir)
        archive_dir = os.path.realpath(archive_dir)
        out_dir_0 = os.path.join(archive_dir, patient_id)
        if not os.path.exists(out_dir_0):
            os.mkdir(out_dir_0)
        out_dir_1 = os.path.join(out_dir_0, md5sum)
        out_path = None
        # if output was not previously written, write it now
        if os.path.exists(out_dir_1):
            msg = "Output directory {0} exists; ".format(out_dir_1)+\
                  "an identical file has already been archived; not writing to archive"
            self.logger.info(msg)
        else:
            os.mkdir(out_dir_1)
            out_path = os.path.join(out_dir_1, "{0}.json".format(self.patient_id))
            with open(out_path, 'w') as out_file:
                out_file.write(data_string)
            msg = "Archived JSON to {0}".format(out_path)
