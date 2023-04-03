"""Class to configure core INI elements"""

import logging
from djerba.util.logger import logger

class configurer(logger):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def run(self, config):
        # TODO validate config fields and (if possible) populate any not specified
        config['neo'] = 'Neo was here'
        config['trinity'] = 'Trinity was here first'
        return config
