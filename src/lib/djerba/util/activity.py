"""Track activity by the main Djerba script"""

import csv
import json
import logging
import os
import time
from configparser import ConfigParser
import djerba.util.constants as constants
from djerba.core.main import arg_processor
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class activity_tracker(logger):

    """
    Djerba Activity Tracker

    If the DJERBA_TRACKING_DIR environment variable is configured,
    we write a one-line file to that directory, with details of this particular usage of the
    Djerba script. (We write a tiny file, instead of appending to a larger one, to ensure
    there are no collisions between update attempts.) These values can then be collated to 
    get a picture of Djerba usage over time.

    Output fields are:
    1. Timestamp
    2. Username
    3. Script mode (setup, report, update, etc.)
    4. Project
    5. Study
    6. Donor
    7. Requisition ID
    8. Report ID
    9. Working directory name
    10. Working directory parent name
    11. Working directory full path

    Fields are set to the empty string '' if data is not available, eg. in setup mode
    the report ID is not known.

    Note that the working directory and parent (fields 9 and 10) are conventionally named for
    the donor and requisition ID (fields 6 and 7), and can be used as fallback values.
    """

    DJERBA_TRACKING_DIR_VAR = 'DJERBA_TRACKING_DIR'
    LOCK_FILE_NAME = 'djerba_activity_tracker.lock'
    OUTPUT_FILE_PREFIX = 'djerba_activity_'

    DONOR = 'donor'
    PROJECT = 'project'
    STUDY = 'study'
    REQUISITION_ID = 'requisition_id'
    REPORT_ID = 'report_id'
    IDENTIFIER_KEYS = [PROJECT, STUDY, DONOR, REQUISITION_ID, REPORT_ID]

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.log_level = log_level
        self.log_path = log_path
        self.tracking_dir = os.getenv(self.DJERBA_TRACKING_DIR_VAR)
        if self.tracking_dir == None:
            msg = "Variable "+DJERBA_TRACKING_DIR_VAR+" not set, omitting activity tracking"
            self.logger.info(msg)
        else:
            self.validator = path_validator(log_level, log_path)
            try:
                self.validator.validate_output_dir(self.tracking_dir)
            except OSError as err:
                msg = "Cannot process tracking directory '"+self.DJERBA_TRACKING_DIR_VAR+"'"
                self.logger.error(msg)
                raise DjerbaActivityTrackerError(msg) from err

    def append_with_lock(self, fields, out_path):
        # safely append with a lock file to avoid collision between updates
        out_string = "\t".join([str(x) for x in fields])+"\n"
        lock_path = os.path.join(self.tracking_dir, self.LOCK_FILE_NAME)
        delays = [0.01, 0.1, 1, 5]
        short_delay = 0.01
        if os.path.exists(lock_path):
            for delay in delays:
                msg = "Lock path {0} exists, delaying {1}s".format(lock_path, delay) 
                self.logger.debug(msg)
                time.sleep(delay)
                if not os.path.exists(lock_path):
                    break
            # lock path still exists after delays
            msg = "Lock path '{0}' exists after maximum delay; ".format(lock_path)+\
                "may need manual deletion"
            self.logger.error(msg)
            raise DjerbaActivityTrackerError(msg)
        # make the lock file and append to the output file
        open(lock_path, 'a').close()
        time.sleep(short_delay)
        with open(out_path, 'a') as out_file:
            out_file.write(out_string)
        time.sleep(short_delay)
        os.remove(lock_path)

    def get_fields(self, ap):
        mode = ap.get_mode()
        fields = [
            time.strftime('%Y-%m-%d_%H:%M:%S_%z'),
            self.get_user(),
            mode
        ]
        identifiers = {name: '' for name in self.IDENTIFIER_KEYS}
        if mode in [constants.CONFIGURE, constants.EXTRACT, constants.REPORT]:
            ini_path = ap.get_ini_path()
            identifiers = self.update_identifiers_from_ini(identifiers, ini_path)
        elif mode in [constants.RENDER, constants.UPDATE]:
            json_path = ap.get_json()
            identifiers = self.update_identifiers_from_json(identifiers, json_path)
        fields.extend([identifiers[k] for k in self.IDENTIFIER_KEYS])
        cwd = os.getcwd()
        directory = os.path.basename(cwd)
        parent = os.path.basename(os.path.dirname(cwd))
        fields.extend([directory, parent, cwd])
        return fields

    def get_user(self):
        # Return the sudo username, in preference to the current effective username
        if os.getenv('SUDO_USER'):
            return os.getenv('SUDO_USER')
        else:
            return os.getenv('USER')

    def run(self, args):
        """
        Write a file to the tracking directory, to record this instance of usage
        Input is the arguments supplied to the djerba.py script
        Output is a tab-delimited set of fields
        """
        # get path for output
        out_file_name = self.OUTPUT_FILE_PREFIX+time.strftime('%Y-%m-%d')
        out_path = os.path.join(self.tracking_dir, out_file_name)
        # generate the output fields
        ap = arg_processor(args, logger=self.logger)
        fields = self.get_fields(ap)
        # append to file
        self.append_with_lock(fields, out_path)
        self.logger.info("Activity tracking written to "+out_path)

    def update_identifiers_from_ini(self, identifiers, ini_path):
        # TODO check compatibility with TAR/PWGS INI files
        self.validator.validate_input_file(ini_path)
        cp = ConfigParser()
        cp.read(ini_path)
        if cp.has_section('input_params_helper'):
            # if input_params_helper absent, we could also get from case_overview
            # but for simplicity, we just use input_params_helper
            for key in [self.DONOR, self.PROJECT, self.STUDY, self.REQUISITION_ID]:
                identifiers[key] = cp.get('input_params_helper', key)
        if cp.has_option('case_overview', self.REPORT_ID):
            identifiers[self.REPORT_ID] = cp.get('case_overview', self.REPORT_ID)
        return identifiers

    def update_identifiers_from_json(self, identifiers, json_path):
        # TODO check compatibility with TAR/PWGS JSON files
        self.validator.validate_input_file(json_path)
        with open(json_path, encoding=constants.TEXT_ENCODING) as json_file:
            data = json.load(json_file)
        config = data['config']
        for key in [self.DONOR, self.PROJECT, self.STUDY, self.REQUISITION_ID]:
            identifiers[key] = config['input_params_helper'][key]
        identifiers[self.REPORT_ID] = config['case_overview'][self.REPORT_ID]
        return identifiers

class DjerbaActivityTrackerError(Exception):
    pass

