"""Class to configure core INI elements"""

import logging
import djerba.util.ini_fields as ini
from djerba.util.logger import logger

class configurer(logger):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def configure(self, config):
        # TODO validate config fields and (if possible) populate any not specified
        config.set(ini.CORE, 'comment', 'Djerba 1.0 under development')
        return config

    def get_default_config_priority(self):
        return 0
