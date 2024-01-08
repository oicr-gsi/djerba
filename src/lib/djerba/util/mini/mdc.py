"""
Mini-Djerba config class
INI and free-text block nested inside XML tags
"""

import logging
import re
import djerba.core.constants as core_constants
from configparser import ConfigParser
from djerba.plugins.patient_info.plugin import main as plugin
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class mdc(logger):

    PATIENT_INFO_KEYS = [
        plugin.PATIENT_NAME,
        plugin.PATIENT_DOB,
        plugin.PATIENT_SEX,
        plugin.REQ_EMAIL,
        plugin.PHYSICIAN_LICENCE,
        plugin.PHYSICIAN_NAME,
        plugin.PHYSICIAN_PHONE,
        plugin.PHYSICIAN_HOSPITAL
    ]

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(self.log_level, self.log_path) 

    def read(self, in_path):
        self.validator.validate_input_file(in_path)
        with open(in_path, encoding=core_constants.TEXT_ENCODING) as in_file:
            in_lines = in_file.readlines()
        # Read INI lines up to a ### marker, then switch to the free text section
        # include empty [core] and [summary] sections for later use
        ini = [
            "[core]\n\n",
            "[summary]\n\n"
            "[patient_info]\n",
        ]
        text = []
        ini_section = True
        for line in lines:
            if re.search('###', line):
                ini_section = False
            elif ini_section:
                if re.search('\S+', line): # line is not whitespace-only
                    ini.append(line)
            else:
                text.append(line)
        self.text = ''.join(text).strip() # leading/trailing whitespace is removed
        self.config = ConfigParser().read_string(''.join(ini))
        self.logger.info("Read MDC file from {0}".format(in_path))

    def write(self, out_path, config, text):
        self.validator.validate_output_file(out_path)
        with open(out_path, 'w', encoding=core_constants.TEXT_ENCODING) as out_file:
            for key in self.PATIENT_INFO_KEYS:
                value = config.get('patient_info', key)
                print("{0} = {1}".format(key, value), file=out_file)
            print("\n###\n", file=out_file)
            print(text, file=out_file)
        self.logger.info("Wrote MDC file to {0}".format(out_path))

    def get_text(self):
        return self.text

    def get_config(self):
        return self.config


class MDCError(Exception):
    pass
