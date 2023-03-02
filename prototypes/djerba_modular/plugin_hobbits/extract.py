"""Extract params given the INI file and write as JSON"""

import json
import logging
import os
import djerba_modular.plugin_hobbits.constants as constants
import djerba_modular.plugin_hobbits.ini as ini
import djerba.util.constants as djerba_constants
from djerba.util.logger import logger
from djerba_modular.plugin_hobbits import PLUGIN_NAME

class extractor(logger):

    def __init__(self, config, work_dir, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.config = config
        self.work_dir = work_dir

    def run(self):
        in_path = self.config[PLUGIN_NAME][ini.FIZ]
        with open(in_path) as in_file:
            content = in_file.read().strip()
        data = {
            djerba_constants.REPORT: {
                PLUGIN_NAME: {
                    constants.ROHAN: self.config[PLUGIN_NAME][ini.FOO],
                    constants.GONDOR: self.config[PLUGIN_NAME][ini.BAR],
                    constants.SHIRE: self.config[PLUGIN_NAME][ini.BAZ],
                    constants.RING: content
                }
            }
        }
        with open(os.path.join(self.work_dir, "{0}.json".format(PLUGIN_NAME)), 'w') as out_file:
            out_file.write(json.dumps(data))
        return data
