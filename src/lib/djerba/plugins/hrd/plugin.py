"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import re
import logging
import json

from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    PRIORITY = 2000
    PLUGIN_VERSION = '1.0'
    TEMPLATE_NAME = 'template.html'
    HRDETECT_PATH = 'hrd_path'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        if wrapper.my_param_is_null(self.HRDETECT_PATH):
            path_info = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
            hrdetect_path = path_info.get('hrDetect')
            if hrdetect_path == None:
                msg = 'Cannot find hrdetect path for HRD input'
                self.logger.error(msg)
                raise RuntimeError(msg)
            wrapper.set_my_param(self.HRDETECT_PATH, hrdetect_path)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        hrd_path = config[self.identifier][self.HRDETECT_PATH]
        hrd_file = open(hrd_path)
        hrd_data = json.load(hrd_file)
        hrd_file.close()
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        out_path = os.path.join(work_dir, 'hrd.tmp.txt')
        try:
            os.remove(out_path)
        except OSError:
            pass
        for row in hrd_data["hrdetect_call"]:
            self.write_hrd(out_path, row, hrd_data["hrdetect_call"][row])
        hrd_base64 = self.write_plot(work_dir)       
        if hrd_data["hrdetect_call"]["Probability.w"][1] > 0.7:
            HRD_long = "Homologous Recombination Deficiency (HR-D)"
            HRD_short = "HR-D"
        else:
            HRD_long = "Homologous Recombination Proficiency (HR-P)"
            HRD_short = "HR-P"
        results =  {
                'files': 
                    {'hrd_path': hrd_path},
                'HRD-score': hrd_data["hrdetect_call"]["Probability.w"],
                'HRD_long': HRD_long,
                'HRD_short': HRD_short,
                'QC' : hrd_data["QC"],
                'hrd_base64' : hrd_base64
            }
        self.workspace.write_json('hrd.json', hrd_data)
        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        discovered = [
            self.HRDETECT_PATH
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'research')
        self.set_priority_defaults(self.PRIORITY)

    def write_hrd(self, out_path, row, quartiles):
        with open(out_path, 'a') as out_file:
            print("\t".join((row,"\t".join([str(item) for item in list(quartiles)]))), file=out_file)
        return out_path

    def write_plot(self, output_dir ):
        args = [
            os.path.join(os.path.dirname(__file__),'plot.R'),
            '--dir', output_dir
        ]
        pwgs_results = subprocess_runner().run(args)
        return(pwgs_results.stdout.split('"')[1])