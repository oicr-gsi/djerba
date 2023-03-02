"""Find relevant data from JSON and render HTML"""

import json
import logging
import os
import djerba_modular.plugin_wise.ini as ini
import djerba.util.constants as djerba_constants
from djerba.util.logger import logger
from djerba_modular.plugin_wise import PLUGIN_NAME
from mako.lookup import TemplateLookup

class renderer(logger):

    def __init__(self, data, work_dir, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.data = data[PLUGIN_NAME]
        self.work_dir = work_dir
        html_dir = os.path.dirname(__file__)
        report_lookup = TemplateLookup(directories=[html_dir,], strict_undefined=True)
        self.template = report_lookup.get_template("template_wise.html")
        
    def run(self):
        args = {'data': self.data}
        html = self.template.render(**args)
        out_path = os.path.join(self.work_dir, "{0}.html".format(PLUGIN_NAME))
        with open(out_path, 'w') as out_file:
            out_file.write(html)
        return out_path
