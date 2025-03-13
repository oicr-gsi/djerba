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
import shutil
import djerba.core.constants as cc
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

    def abs_path(self, rel_path):
        """Return the absolute path of a file in the workspace"""
        return os.path.abspath(os.path.join(self.dir_path, rel_path))

    def copy_to_workspace(self, rel_path):
        """Copies the path to the workspace. Returns None."""
        shutil.copy(rel_path, self.dir_path)

    def get_work_dir(self):
        return self.dir_path

    def has_file(self, rel_path):
        return os.path.exists(os.path.join(self.dir_path, rel_path))

    def open_gzip_file(self, rel_path, write=False):
        if write:
            mode = 'wt'
        else:
            mode = 'rt'
        in_path = os.path.join(self.dir_path, rel_path)
        if not write:
            self.validator.validate_input_file(in_path)
        return gzip.open(in_path, mode)

    def open_file(self, rel_path, mode='r'):
        """Return a File object, eg. for use by csv.reader or csv.writer"""
        file_path = os.path.join(self.dir_path, rel_path)
        if 'r' in mode:
            self.validator.validate_input_file(file_path)
        else:
            self.validator.validate_output_file(file_path)
        return open(file_path, mode, encoding=cc.TEXT_ENCODING)

    def print_location(self):
        return self.dir_path

    def read_json(self, rel_path):
        in_path = os.path.join(self.dir_path, rel_path)
        self.validator.validate_input_file(in_path)
        with open(in_path, encoding=cc.TEXT_ENCODING) as in_file:
            data = json.loads(in_file.read())
        return data

    def read_maybe_input_params(self):
        # convenience method to read the input_params.json (if any)
        return self.read_maybe_json('input_params.json')

    def read_maybe_json(self, rel_path):
        # if JSON file exists, read it and return the data; otherwise return None
        # typically, this is used in plugin config with fallback to manual inputs
        data = None
        if self.has_file(rel_path):
            data = self.read_json(rel_path)
            self.logger.debug("Read JSON from {0}".format(rel_path))
        else:
            msg = "{0} not found; may use manual inputs if available".format(rel_path)
            self.logger.info(msg)
        return data

    def read_string(self, rel_path):
        in_path = os.path.join(self.dir_path, rel_path)
        self.validator.validate_input_file(in_path)
        with open(in_path, encoding=cc.TEXT_ENCODING) as in_file:
            content = in_file.read()
        return content

    def remove_file(self, rel_path):
        os.remove(os.path.join(self.dir_path, rel_path))
    
    # no need to validate paths for write_* methods; output dir already validated as writable

    def write_json(self, rel_path, data):
        out_path = os.path.join(self.dir_path, rel_path)
        with open(out_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
            out_file.write(json.dumps(data))

    def write_string(self, rel_path, output_string):
        out_path = os.path.join(self.dir_path, rel_path)
        with open(out_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
            out_file.write(output_string)
