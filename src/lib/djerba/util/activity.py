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

    If the DJERBA_TRACKING_DIR environment variable is configured, we append to a file
    in that directory, with details of this particular usage of the djerba.py script.

    The file is named for the current date, 'djerba_activity_YYYY-MM-DD.tsv'.

    Output fields are:
    1. Timestamp
    2. Username
    3. Script mode (setup, report, update, etc.)
    4. Assay
    5. Project
    6. Study
    7. Donor
    8. Requisition ID
    9. Report ID
    10. INI path
    11. JSON path
    12. Working directory name
    13. Working directory parent name
    14. Working directory full path

    The output file has a header line with the field names, prefixed by '#'.

    Fields are set to the empty string '' if data is not available, eg. in setup mode
    the report ID is not known.

    The working directory and parent (fields 9 and 10) are conventionally named for
    the donor and requisition ID (fields 6 and 7), and can be used as fallback values.

    Usage of `djerba.py` with the `-h` or `--help` option is not recorded.

    Tracking is done before the main Djerba functions start -- so if `djerba.py` exits
    with an error, it has still been recorded by activity tracking.
    """

    DJERBA_TRACKING_DIR_VAR = 'DJERBA_TRACKING_DIR'
    LOCK_FILE_NAME = 'djerba_activity_tracker.lock'
    OUTPUT_FILE_PREFIX = 'djerba_activity_'

    ASSAY = 'assay'
    DONOR = 'donor'
    PROJECT = 'project'
    STUDY = 'study'
    REQUISITION_ID = 'requisition_id'
    REPORT_ID = 'report_id'
    INI_PATH = 'ini_path'
    JSON_PATH = 'json_path'
    IDENTIFIER_KEYS = [ASSAY, PROJECT, STUDY, DONOR, REQUISITION_ID,
                       REPORT_ID, INI_PATH, JSON_PATH]
    HEADERS = ['#time', 'user', 'mode', 'assay', 'project', 'study', 'donor',
               'requisition_id', 'report_id', 'ini', 'json',
               'cwd_name', 'cwd_parent_name', 'cwd']

    def __init__(self, log_level=logging.WARNING, log_path=None, timeout_multiplier=1):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.log_level = log_level
        self.log_path = log_path
        self.timeout_multiplier = float(timeout_multiplier) # use to modify timeout duration
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
        delays = [x*self.timeout_multiplier for x in [0.01, 0.1, 1, 5]]
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
        if os.path.exists(out_path):
            write_header = False
        else:
            write_header = True
        with open(out_path, 'a') as out_file:
            if write_header:
                out_file.write('\t'.join(self.HEADERS)+"\n")
            out_file.write(out_string)
        time.sleep(short_delay)
        os.remove(lock_path)

    def get_fields(self, ap):
        # get timestamp, username, script mode
        mode = ap.get_mode()
        fields = [
            time.strftime('%Y-%m-%d_%H:%M:%S_%z'),
            self.get_user(),
            mode
        ]
        # get assay, project, study, donor, requisition id, report id (if available)
        identifiers = {name: '' for name in self.IDENTIFIER_KEYS}
        if mode == constants.SETUP:
            identifiers[self.ASSAY] = ap.get_assay()
        elif mode in [constants.CONFIGURE, constants.EXTRACT, constants.REPORT]:
            ini_path = ap.get_ini_path()
            identifiers = self.update_identifiers_from_ini(identifiers, ini_path)
        elif mode in [constants.RENDER, constants.UPDATE]:
            json_path = ap.get_json()
            identifiers = self.update_identifiers_from_json(identifiers, json_path)
        fields.extend([identifiers[k] for k in self.IDENTIFIER_KEYS])
        # get directory names and path
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
        out_file_name = self.OUTPUT_FILE_PREFIX+time.strftime('%Y-%m-%d')+'.tsv'
        out_path = os.path.join(self.tracking_dir, out_file_name)
        # generate the output fields
        ap = arg_processor(args, logger=self.logger)
        fields = self.get_fields(ap)
        # append to file
        self.append_with_lock(fields, out_path)
        self.logger.info("Activity tracking written to "+out_path)

    def update_identifiers_from_ini(self, identifiers, ini_path):
        # This is compatible with TAR/PWGS INI files
        self.validator.validate_input_file(ini_path)
        identifiers[self.INI_PATH] = ini_path
        cp = ConfigParser()
        cp.read(ini_path)
        if cp.has_section('tar.sample'):
            identifiers[self.ASSAY] = 'TAR'
        elif cp.has_section('pwgs.sample'):
            identifiers[self.ASSAY] = 'PWGS'
        elif cp.has_section('expression_helper'):
            identifiers[self.ASSAY] = 'WGTS'
        elif cp.has_section('sample'):
            identifiers[self.ASSAY] = 'WGS'
        # no input params helper for PWGS
        for section in ['input_params_helper', 'tar_input_params_helper']:
            if cp.has_section(section):
                ip_keys = [self.DONOR, self.PROJECT, self.STUDY, self.REQUISITION_ID]
                for key in ip_keys:
                    identifiers[key] = cp.get(section, key)
                break
        # TAR uses same case overview plugin as WGTS
        for section in ['case_overview', 'pwgs.case_overview']:
            if cp.has_option(section, self.REPORT_ID):
                identifiers[self.REPORT_ID] = cp.get(section, self.REPORT_ID)
                break
        return identifiers

    def update_identifiers_from_json(self, identifiers, json_path):
        # TODO check compatibility with TAR/PWGS JSON files
        self.validator.validate_input_file(json_path)
        identifiers[self.JSON_PATH] = json_path
        with open(json_path, encoding=constants.TEXT_ENCODING) as json_file:
            data = json.load(json_file)
        config = data['config']
        for key in [self.DONOR, self.PROJECT, self.STUDY, self.REQUISITION_ID]:
            identifiers[key] = config['input_params_helper'][key]
        identifiers[self.ASSAY] = config['case_overview'][self.ASSAY]
        identifiers[self.REPORT_ID] = config['case_overview'][self.REPORT_ID]
        return identifiers

class DjerbaActivityTrackerError(Exception):
    pass

