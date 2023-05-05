"""Class to configure core INI elements"""

import logging
import djerba.util.ini_fields as ini
from djerba.core.configurable import configurable

class configurer(configurable):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_ini_default('comment', 'comment goes here')

    def configure(self, config):
        # TODO validate config fields and (if possible) populate any not specified
        config.set(ini.CORE, 'comment', 'Djerba 1.0 under development')
        return config

    def get_default_config_priority(self):
        return 0
