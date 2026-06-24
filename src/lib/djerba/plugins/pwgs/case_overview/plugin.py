"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
import json

from djerba.plugins.base import plugin_base
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.render_mako import mako_renderer
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools
import djerba.plugins.pwgs.constants as pc
import djerba.util.assays as assays

class main(plugin_base):
    PRIORITY = 100
    PLUGIN_VERSION = '1.0'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        if os.path.exists(os.path.join(work_dir, core_constants.DEFAULT_SAMPLE_INFO)):
            sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            if wrapper.my_param_is_null(pc.DONOR):
                wrapper.set_my_param(pc.DONOR, sample_info[pc.DONOR])
            if wrapper.my_param_is_null(pc.GROUP_ID):
                # set group_id to tumour_id when unspecified
                wrapper.set_my_param(pc.GROUP_ID, sample_info[core_constants.TUMOUR_ID])
            if wrapper.my_param_is_null(pc.PATIENT_ID_LOWER):
                wrapper.set_my_param(pc.PATIENT_ID_LOWER, sample_info[pc.PATIENT_ID_LOWER])
        else:
            msg = 'sample info file not found, make sure case overview parameters are in INI'
            self.logger.warning(msg)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        assay = "plasma Whole Genome Sequencing (pWGS) - "+\
            "30X (v{0})".format(assays.PWGS_ASSAY_VERSION)
        results = {
            pc.ASSAY: assay,
            pc.PWGS_REPORT: config['core']['report_id'],
            pc.PRIMARY_CANCER: config[self.identifier][pc.PRIMARY_CANCER],
            pc.REQ_APPROVED: config[self.identifier][pc.REQ_APPROVED],
            pc.DONOR: config[self.identifier][pc.DONOR],
            pc.GROUP_ID: config[self.identifier][pc.GROUP_ID],
            pc.PATIENT_ID: config[self.identifier][pc.PATIENT_ID_LOWER],
            pc.STUDY: config[self.identifier][pc.STUDY],
            pc.WGS_REPORT: config[self.identifier][pc.WGS_REPORT]
        }
        data[pc.RESULTS] = results
        self.workspace.write_json('pWGS_case_overview_output.json', data)
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.CASE_OVERVIEW_TEMPLATE_NAME, data)

    def specify_params(self):
        required = [
            pc.REQ_APPROVED,
            pc.PRIMARY_CANCER,
            pc.WGS_REPORT, 
            pc.STUDY
        ]
        for key in required:
            self.add_ini_required(key)
        discovered = [
            pc.DONOR,
            pc.GROUP_ID,
            pc.PATIENT_ID_LOWER,
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)


