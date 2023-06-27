"""Main interface for the plugin"""

import json
import os

from configparser import ConfigParser

import djerba.util.constants as djerba_constants
from djerba_modular.core.plugin_main import main as main_core
from djerba_modular.plugin_hobbits import PLUGIN_NAME
from djerba_modular.plugin_hobbits.configure import configurer
from djerba_modular.plugin_hobbits.extract import extractor
from djerba_modular.plugin_hobbits.render import renderer

class main(main_core):

    def configure(self, ini_path, work_dir):
        cp = ConfigParser()
        cp.read(ini_path)
        out_path = os.path.join(work_dir, '{0}_full_config.ini'.format(PLUGIN_NAME))
        new_cp = configurer(cp).run(out_path)
        return new_cp[PLUGIN_NAME]
    
    def extract(self, ini_path, work_dir):
        cp = ConfigParser()
        cp.read(ini_path)
        data = extractor(cp, work_dir, self.log_level, self.log_path).run()
        return data[djerba_constants.REPORT]

    def render(self, json_path, work_dir):
        with open(json_path) as json_file:
            data = json.loads(json_file.read())
        return renderer(data, work_dir, self.log_level, self.log_path).run()
