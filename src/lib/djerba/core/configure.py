"""Class to configure core INI elements"""

import logging
import djerba.util.ini_fields as ini
from djerba.core.configurable import configurable

class configurer(configurable):

    def __init__(self, log_level=logging.INFO, log_path=None):
        super().__init__(ini.CORE, log_level, log_path)
        #self.set_ini_default('comment', 'comment goes here')

        # Setting required parameters
        self.add_ini_required('tumour_id')
        self.add_ini_required('study_title')
        self.add_ini_required('root_sample_name')

    def configure(self, config):
        # TODO validate config fields and (if possible) populate any not specified
        #config.set(ini.CORE, 'comment', 'Djerba 1.0 under development')
        return config

    def get_default_config_priority(self):
        return 0
