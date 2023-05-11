"""
Class to represent a directory for temporary data files:
- Similar to the report directory in classic Djerba
- Open/read/write methods take paths relative to the workspace directory
- Workspace files are *not* intended for long-term archival
- Data needed long-term should be recorded in the report JSON file
"""

import gzip
import json
import logging
import os
from djerba.util.logger import logger
from djerba.util.validator import path_validator


class workspace(logger):

    def __init__(self, dir_path, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(self.log_level, self.log_path)
        self.validator.validate_output_dir(dir_path)
        self.dir_path = dir_path

    def open_gzip_file(self, rel_path, write=False):
        if write:
            mode = 'wt'
        else:
            mode = 'rt'
        in_path = os.path.join(self.dir_path, rel_path)
        if not write:
            self.validator.validate_input_file(in_path)
        return gzip.open(in_path, mode)

    def open_file(self, rel_path):
        """Return a File object in read mode, eg. for use by csv.reader"""
        in_path = os.path.join(self.dir_path, rel_path)
        self.validator.validate_input_file(in_path)
        return open(in_path)
    
    def print_location(self):
        return(self.dir_path)

    def read_json(self, rel_path):
        in_path = os.path.join(self.dir_path, rel_path)
        self.validator.validate_input_file(in_path)
        with open(in_path) as in_file:
            data = json.loads(in_file.read())
        return data

    def read_string(self, rel_path):
        in_path = os.path.join(self.dir_path, rel_path)
        self.validator.validate_input_file(in_path)
        with open(in_path) as in_file:
            content = in_file.read()
        return content

    # no need to validate paths for write_* methods; output dir already validated as writable

    def write_json(self, rel_path, data):
        with open(os.path.join(self.dir_path, rel_path), 'w') as out_file:
            out_file.write(json.dumps(data))

    def write_string(self, rel_path, output_string):
        with open(os.path.join(self.dir_path, rel_path), 'w') as out_file:
            out_file.write(output_string)
