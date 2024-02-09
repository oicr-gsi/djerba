"""
Mini-Djerba config class
INI and free-text block separated by ###
"""

import logging
import re
import djerba.core.constants as core_constants
from configparser import ConfigParser, NoOptionError
from time import strftime
from djerba.plugins.patient_info.plugin import main as patient_info_plugin
from djerba.plugins.supplement.body.plugin import main as supplement_plugin
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class mdc(logger):

    MDC = 'mdc'
    MDC_HEADER = '['+MDC+']'

    PATIENT_INFO_KEYS = [
        patient_info_plugin.PATIENT_NAME,
        patient_info_plugin.PATIENT_DOB,
        patient_info_plugin.PATIENT_SEX,
        patient_info_plugin.REQ_EMAIL,
        patient_info_plugin.PHYSICIAN_LICENCE,
        patient_info_plugin.PHYSICIAN_NAME,
        patient_info_plugin.PHYSICIAN_PHONE,
        patient_info_plugin.PHYSICIAN_HOSPITAL
    ]

    SUPPLEMENT_KEYS = [
        supplement_plugin.REPORT_SIGNOFF_DATE,
        supplement_plugin.GENETICIST,
        supplement_plugin.GENETICIST_ID
    ]

    CONFIG_KEYS = PATIENT_INFO_KEYS + SUPPLEMENT_KEYS

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(self.log_level, self.log_path) 

    def read(self, in_path):
        """
        Input: Path to a .mdc config file
        Output: Dictionaries of params, and string containing summary text
        """
        self.validator.validate_input_file(in_path)
        with open(in_path, encoding=core_constants.TEXT_ENCODING) as in_file:
            in_lines = in_file.readlines()
        self.sanity_check(in_lines)
        # Read INI lines up to a ### marker, then switch to the free text section
        ini_lines = [self.MDC_HEADER+"\n"] # temporary header for INI string parsing
        text_lines = []
        ini_section = True
        for line in in_lines:
            if re.search('###', line):
                ini_section = False
            elif ini_section:
                ini_lines.append(line)
            else:
                text_lines.append(line)
        text = ''.join(text_lines).strip() # leading/trailing whitespace is removed
        config = ConfigParser()
        config.read_string(''.join(ini_lines))
        try:
            patient_info = {k:config.get(self.MDC, k) for k in self.PATIENT_INFO_KEYS}
            supplement = {k:config.get(self.MDC, k) for k in self.SUPPLEMENT_KEYS}
        except NoOptionError as err:
            msg = "Missing one or more key=value pairs. MDC file must have values "+\
                "for the following keys: {0}".format(', '.join(self.CONFIG_KEYS))
            self.logger.error(msg)
            raise MDCFormatError(msg) from err
        self.logger.info("Read MDC file from {0}".format(in_path))
        return [patient_info, supplement, text]

    def sanity_check(self, lines):
        """
        Sanity check on config input
        Not intended to be foolproof, but should catch obvious errors
        """
        ini_section = True
        has_ini = False
        has_separator = False
        has_text = False
        for line in lines:
            if re.search('###', line):
                ini_section = False
                has_separator = True
            elif ini_section:
                if re.search('\s*\w+\s*=\s*\w+', line):
                    has_ini = True
                elif not re.search('^\s+$', line):
                    msg = 'INI section line should be key=value or empty space, '+\
                        'found "{0}"'.format(line.strip())
                    self.logger.error(msg)
                    raise MDCFormatError(msg)
            elif re.search('\S+', line):
                has_text = True
        err = None
        if not has_separator:
            err = "MDC file must contain a section separator of the form '###', none found"
        elif not has_ini:
            err = "MDC file must contain key=value pairs, none found"
        elif not has_text:
            err = "MDC file must contain non-empty summary text, none found"
        if err:
            self.logger.error(err)
            raise MDCFormatError(err)

    def write(self, out_path, patient_info, supplement, text, auto_signoff_date=True):
        """
        Input: Dictionaries of patient info & supplement, and string containing summary text
        Dictionaries may contain additional keys, which will be ignored
        """
        self.validator.validate_output_file(out_path)
        with open(out_path, 'w', encoding=core_constants.TEXT_ENCODING) as out_file:
            for key in self.PATIENT_INFO_KEYS:
                value = patient_info.get(key)
                print("{0} = {1}".format(key, value), file=out_file)
            for key in self.SUPPLEMENT_KEYS:
                if key == supplement_plugin.REPORT_SIGNOFF_DATE and auto_signoff_date:
                    value = strftime('%Y/%m/%d')
                else:
                    value = supplement.get(key)
                print("{0} = {1}".format(key, value), file=out_file)
            print("\n###\n", file=out_file)
            print(text, file=out_file)
        self.logger.info("Wrote MDC file to {0}".format(out_path))

class MDCFormatError(Exception):
    pass
