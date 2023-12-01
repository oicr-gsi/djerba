"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
import json
import requests

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as pc
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools
from djerba.util.render_mako import mako_renderer
from djerba.util.provenance_reader import provenance_reader

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
    raise ImportError('Error Importing QC-ETL, try checking python versions')

class main(plugin_base):

    PRIORITY = 100
    PLUGIN_VERSION = '1.0'
    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        patient_data = self.preprocess_wgs_json(config[self.identifier][pc.WGS_JSON])
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        results =  {
                pc.REQ_APPROVED: config[self.identifier][pc.REQ_APPROVED],
                pc.GROUP_ID: config[self.identifier][pc.GROUP_ID],
                'assay': "plasma Whole Genome Sequencing (pWGS) - 30X (v1.0)",
                'primary_cancer': patient_data['Primary cancer'],
                'donor': patient_data['Patient LIMS ID'],
                'wgs_report_id': patient_data['Report ID'],
                'Patient Study ID': patient_data[pc.PATIENT_ID],
                'study_title':  config[self.identifier]['study_id'],
                'pwgs_report_id': config['core']['report_id']
            }
        data[pc.RESULTS] = results
        return data

    def preprocess_wgs_json(self, wgs_json):
        '''find patient info from WGS/WGTS djerba report json'''
        with open(wgs_json, 'r') as wgs_results:
            data = json.load(wgs_results)
        patient_data = data["report"]["patient_info"]
        return(patient_data)
    
    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.CASE_OVERVIEW_TEMPLATE_NAME, data)
    
    def specify_params(self):
        required = [
            pc.REQ_APPROVED,
            pc.GROUP_ID,
            pc.WGS_JSON,
            'study_id'
        ]
        for key in required:
            self.add_ini_required(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

