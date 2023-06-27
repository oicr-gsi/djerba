"""Configure an INI file with Djerba inputs"""

import logging

import djerba.util.ini_fields as base_ini
import djerba_modular.plugin_wise
import djerba_modular.plugin_wise.ini as ini

from djerba_modular.plugin_wise import PLUGIN_NAME
from djerba.util.logger import logger
from djerba.util.validator import config_plugin_validator

# bare-bones configuration demo:
# - validate the INI inputs (previously done in main.py)
# - discover additional parameters (if any)
# - write out the fully-specified INI file: includes core params, can be used for extract step
#
# General design notes:
# - Assume a separate output directory for each plugin (eg. create in base report dir)
# - The 'demo' classes may be sufficiently abstract to import (or subclass) for multiple plugins
# - ie. the demo classes may become general-purpose 'plugin runners'

class configurer(logger):

    def __init__(self, config, log_level=logging.INFO, log_path=None):
        self.config = config
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        schema = base_ini.SCHEMA_CORE # settings and core params
        self.logger.info("Configuring Djerba for {0}".format(PLUGIN_NAME))
        self.validator = config_plugin_validator(schema,
                                                 PLUGIN_NAME,
                                                 ini.SCHEMA_REQUIRED,
                                                 ini.SCHEMA_OPTIONAL,
                                                 self.log_level,
                                                 self.log_path)

    def get_config(self):
        return self.config

    def run(self, out_path):
        # validate and update the config; write the results
        self.validator.validate_minimal(self.config)
        self.update()
        self.validator.validate_full(self.config)
        with open(out_path, 'w') as out_file:
            self.config.write(out_file)
        self.logger.info("Wrote fully specified config to {0}".format(out_path))
        return self.config

    def update(self):
        # discover additional input params, if required
        # simplest possible example -- insert a hard-coded string
        self.config[PLUGIN_NAME][ini.BAZ] = '/.mounts/labs/CGI/scratch/ibancarz/djerba_modular_demo_data/saruman.txt'
