"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
import json

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as pc
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools
from djerba.util.render_mako import mako_renderer
from djerba.util.provenance_reader import provenance_reader
import requests

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
    raise ImportError('Error Importing QC-ETL, try checking python versions')

class main(plugin_base):

    PRIORITY = 130
    PLUGIN_VERSION = '1.0'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        if wrapper.my_param_is_null(pc.RESULTS_FILE):
            path_info = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
            results_path = path_info.get(pc.RESULTS_SUFFIX)
            if results_path == None:
                msg = 'Cannot find results path for mrdetect input'
                self.logger.error(msg)
                raise RuntimeError(msg)
            wrapper.set_my_param(pc.RESULTS_FILE, results_path)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        mrdetect_results = pwgs_tools.preprocess_results(self, config[self.identifier][pc.RESULTS_FILE])
        if mrdetect_results[pc.CTDNA_OUTCOME] == "DETECTED":
            ctdna_detection = "Detected"
        elif mrdetect_results[pc.CTDNA_OUTCOME] == "UNDETECTED":
            ctdna_detection = "Undetected"
        else:
            ctdna_detection = None
            self.logger.info("PWGS SAMPLE: ctDNA inconclusive")
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        results =  {
                pc.CTDNA_OUTCOME: mrdetect_results[pc.CTDNA_OUTCOME],
                'ctdna_detection': ctdna_detection
            }
        data[pc.RESULTS] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.SUMMARY_TEMPLATE_NAME, data)
    
    def specify_params(self):
        discovered = [
            pc.RESULTS_FILE
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

