#! /usr/bin/env python3

"""High-level class to run plugins; does split/merge on INI, JSON, HTML"""

import importlib
import json
import logging
import os
from configparser import ConfigParser
from mako.lookup import TemplateLookup

import djerba.util.ini_fields as ini
from djerba.util.logger import logger
from djerba.util.validator import path_validator

### for main() command-line method
import sys
###

class plugin_runner(logger):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)

    def _get_plugin_work_dir(self, base_dir, plugin_name):
        dir_path = os.path.join(base_dir, plugin_name)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        else:
            self.validator.validate_output_dir(dir_path)
        return dir_path

    def _import_plugin_main(self, plugin_name):
        return importlib.import_module('djerba_modular.{0}.plugin_main'.format(plugin_name))

    def configure(self, in_path, out_path, work_dir):
        # writes/returns INI
        self.validator.validate_output_dir(work_dir)
        old_cp = ConfigParser()
        old_cp.read(in_path)
        new_config = {}
        for section in old_cp.sections():
            if section in [ini.SETTINGS, ini.CORE]:
                new_config[section] = old_cp[section]
            else:
                plugin_work_dir = self._get_plugin_work_dir(work_dir, section)
                plugin_main = self._import_plugin_main(section).main(self.log_level, self.log_path)
                new_config[section] = plugin_main.configure(in_path, plugin_work_dir)
        new_cp = ConfigParser()
        new_cp.read_dict(new_config)
        with open(out_path, 'w') as out_file:
            new_cp.write(out_file)
        return new_cp

    def extract(self, in_path, out_path, work_dir):
        # writes/returns JSON
        self.validator.validate_output_dir(work_dir)
        # TODO class in core.extract to extract data using core params only (if needed)
        data = {
            'core': {
                'title': 'Lore of Middle-Earth'
            }
        }
        cp = ConfigParser()
        cp.read(in_path)
        for section in cp.sections():
            if section not in [ini.SETTINGS, ini.CORE]:
                self.logger.info("Extracting data for {0}".format(section))
                plugin_work_dir = self._get_plugin_work_dir(work_dir, section)
                plugin_main = self._import_plugin_main(section).main(self.log_level, self.log_path)
                data[section] = plugin_main.extract(in_path, plugin_work_dir).get(section)
        with open(out_path, 'w') as out_file:
            print(json.dumps(data), file=out_file)        
        return data

    def render(self, in_path, out_path, work_dir):
        # writes HTML
        self.validator.validate_output_dir(work_dir)
        with open(in_path) as in_file:
            data = json.loads(in_file.read())
        plugin_html = []
        # TODO get sections from 'report' element of larger JSON structure
        # TODO configure the order in which plugins write output
        for key in data.keys():
            if key!=ini.CORE:
                self.logger.info("Rendering HTML for {0}".format(key))
                plugin_work_dir = self._get_plugin_work_dir(work_dir, key)
                plugin_main = self._import_plugin_main(key).main(self.log_level, self.log_path)
                plugin_html.append(plugin_main.render(in_path, plugin_work_dir))
        data['plugin_html'] = plugin_html
        html_dir = os.path.dirname(__file__)
        report_lookup = TemplateLookup(directories=[html_dir,], strict_undefined=True)
        template = report_lookup.get_template("template.html")
        html = template.render(**data)
        out_path = os.path.join(work_dir, "plugin_demo_report.html")
        with open(out_path, 'w') as out_file:
            out_file.write(html)

def main():
    ini_path = sys.argv[1]
    work_dir = sys.argv[2]
    runner = plugin_runner()
    ini_full = os.path.join(work_dir, 'full_config.ini')
    json_path = os.path.join(work_dir, 'djerba_modular_demo.json')
    html_path = os.path.join(work_dir, 'djerba_modular_demo.html')
    runner.configure(ini_path, ini_full, work_dir)
    runner.extract(ini_full, json_path, work_dir)
    runner.render(json_path, html_path, work_dir)
    
    
if __name__ == '__main__':
    main()

