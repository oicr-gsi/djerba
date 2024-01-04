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
        work_dir = self.workspace.get_work_dir()
        if os.path.exists(os.path.join(work_dir,core_constants.DEFAULT_SAMPLE_INFO)):
            sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            if wrapper.my_param_is_null('donor'):
                wrapper.set_my_param('donor', sample_info['donor'])
            if wrapper.my_param_is_null(pc.GROUP_ID):
                wrapper.set_my_param(pc.GROUP_ID, sample_info['tumour_id'])
            if wrapper.my_param_is_null('patient study id'):
                wrapper.set_my_param('patient study id', sample_info['patient_study_id'])
            if wrapper.my_param_is_null('study_id'):
                wrapper.set_my_param('study_id', sample_info['project'])
        else:
            msg = 'sample info file not found, make sure case overview parameters are in INI'
            self.logger.warning(msg)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        results =  {
                'assay': "plasma Whole Genome Sequencing (pWGS) - 30X (v1.0)",
                'pwgs_report_id': config['core']['report_id'],
                'primary_cancer': config[self.identifier]['primary_cancer'],
                pc.REQ_APPROVED: config[self.identifier][pc.REQ_APPROVED],
                'donor': config[self.identifier]['donor'],
                pc.GROUP_ID: config[self.identifier][pc.GROUP_ID],
                'Patient Study ID': config[self.identifier]['patient study id'],
                'study_title':  config[self.identifier]['study_id'],
                pc.WGS_REPORT: config[self.identifier][pc.WGS_REPORT]
            }
        data[pc.RESULTS] = results
        return data
    
    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.CASE_OVERVIEW_TEMPLATE_NAME, data)
    
    def specify_params(self):
        required = [
            pc.REQ_APPROVED,
            'primary_cancer',
            pc.WGS_REPORT
        ]
        for key in required:
            self.add_ini_required(key)
        discovered = [
            'donor',
            pc.GROUP_ID,
            'patient study id',
            'study_id'
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

