"""
Mini-Djerba config class
Simplified INI with a free-text capability
"""

import logging
import re
from configparser import ConfigParser
from djerba.plugins.patient_info.plugin import main as plugin
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class mdc(logger):

    PERMITTED_KEYS = [
        plugin.PATIENT_NAME,
        plugin.PATIENT_DOB,
        plugin.PATIENT_SEX,
        plugin.REQ_EMAIL,
        plugin.PHYSICIAN_LICENCE,
        plugin.PHYSICIAN_NAME,
        plugin.PHYSICIAN_PHONE,
        plugin.PHYSICIAN_HOSPITAL
    ]

    def __init__(self, in_path, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        path_validator(self.log_level, self.log_path).validate_input_file(in_path)
        with open(in_path) as in_file:
            in_lines = in_file.readlines()
        # sanity-check the lines, extract the free-text input, and parse the rest as INI
        # include empty [core] and [summary] sections for later use
        ini = [
            "[core]\n\n",
            "[summary]\n\n"
            "[patient_info]\n",
        ]
        text = []
        for line in lines:
            if re.match('\w+\s*=', line): # INI-style config line
                key = re.split('=', line).pop(0).strip()
                if key in self.PERMITTED_KEYS:
                    ini.append(line)
                else:
                    msg = "Unknown MDC key '{0}'".format(key)
                    self.logger.error(msg)
                    raise MDCError(msg)
            else: # all other lines, including white-space only, are treated as free text
                text.append(line)
        self.text = ''.join(text).strip() # leading/trailing whitespace is removed
        self.config = ConfigParser().read_string(''.join(ini))
        self.logger.info("Successfully parsed MDC file {0}".format(in_path))

    def get_text(self):
        return self.text

    def get_config(self):
        return self.config


class MDCError(Exception):
    pass
