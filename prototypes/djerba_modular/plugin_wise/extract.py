"""Extract params given the INI file and write as JSON"""

import json
import logging
import os
import djerba_modular.plugin_wise.constants as constants
import djerba_modular.plugin_wise.ini as ini
import djerba.util.constants as djerba_constants
from djerba.util.logger import logger
from djerba_modular.plugin_wise import PLUGIN_NAME

class extractor(logger):

    def __init__(self, config, work_dir, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.config = config
        self.work_dir = work_dir

    def run(self):
        in_path = self.config[PLUGIN_NAME][ini.BAZ]
        with open(in_path) as in_file:
            content = in_file.read().strip()
        data = {
            djerba_constants.REPORT: {
                PLUGIN_NAME: {
                    constants.GREY: self.config[PLUGIN_NAME][ini.FOO],
                    constants.GOLD: self.config[PLUGIN_NAME][ini.BAR],
                    constants.WHITE: content
                }
            }
        }
        with open(os.path.join(self.work_dir, "{0}.json".format(PLUGIN_NAME)), 'w') as out_file:
            out_file.write(json.dumps(data))
        return data
