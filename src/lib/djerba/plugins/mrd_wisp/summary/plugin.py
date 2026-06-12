"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
import json

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.mrd_wisp.constants as pc
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
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
    PLUGIN_NAME = 'mrd_wisp.summary'
    PLUGIN_VERSION = '1.0'
    BOOL_DICT = {True:"Detected", False:"Undetected"}

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

        # Get the MRD call.
        # NOTE: this plugin depends on the results from mrd_wisp.analysis.
        if self.workspace.has_file(pc.MRD_CALL_FILE):
            self.logger.debug("The plugin mrd_wisp.analysis extracted the MRD call to mrd_call.txt. Using extracted value.")
            mrd_call = self.workspace.read_string(pc.MRD_CALL_FILE) == "True"
            wrapper.set_my_param(pc.MRD_CALL, mrd_call)
        else:
            msg = "mrd_call.txt is missing from the workspace. Either run the mrd_wisp.analysis plugin to generate mrd_call.txt, or create a file called mrd_call.txt with either True or False as the value inside."
            self.logger.error(msg)
            raise RuntimeError(msg)

        mrd_call = wrapper.get_boolean(self.PLUGIN_NAME, pc.MRD_CALL)

        results =  {
                pc.CTDNA_OUTCOME: self.BOOL_DICT[mrd_call].upper(),
                pc.CTDNA_DETECTION: self.BOOL_DICT[mrd_call]
            }
        data[pc.RESULTS] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.SUMMARY_TEMPLATE_NAME, data)
    
    def specify_params(self):
        #discovered = [
        #    pc.MRD_CALL
        #]
        #for key in discovered:
        #    self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

