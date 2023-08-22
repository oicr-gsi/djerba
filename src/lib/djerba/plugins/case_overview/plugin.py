"""
Plugin to generate the Case Overview report section

Assay can be specified by:
- Short name, which looks up in a table of known assays
- Full name -- if this parameter is set manually, the short name is ignored
Typically the short name will be used, but the full name is supported as an INI parameter
in case assay names are introduced/changed at short notice
"""

import logging
from time import strftime
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'case_overview_template.html'

    # config/results keys
    # REPORT_ID, DONOR and STUDY from core
    # Patient LIMS ID = DONOR
    ASSAY_SHORT_NAME = "assay short name"
    ASSAY = "assay"
    BLOOD_SAMPLE_ID = "blood sample id"
    PRIMARY_CANCER = "primary cancer"
    REQUISITION_ID = "requisition id"
    REQ_APPROVED_DATE = "requisition approved"
    SAMPLE_ANATOMICAL_SITE = "site of biopsy/surgery"
    STUDY = "study"
    TUMOUR_SAMPLE_ID = "tumour sample id"
    TUMOUR_DEPTH = 80
    NORMAL_DEPTH = 40

    ASSAY_LOOKUP = {
        # WGTS/WGS default to 80X
        'WGTS': 'Whole genome and transcriptome sequencing (WGTS)'+\
        '-80X Tumour, 30X Normal (v3.0)',
        'WGS': 'Whole genome sequencing (WGS)-80X Tumour, 30X Normal (v3.0)',
        # WGTS/WGS at 40X - seldom done now, but included for completeness
        'WGTS40X': 'Whole genome and transcriptome sequencing (WGTS)'+\
        '-40X Tumour, 30X Normal (v3.0)',
        'WGS40X': 'Whole genome sequencing (WGS)-40X Tumour, 30X Normal (v3.0)',
        # TAR
        'TAR': 'Targeted Sequencing - REVOLVE Panel - cfDNA and Buffy Coat (v1.0)'
    }

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        report_id = wrapper.get_core_string(core_constants.REPORT_ID)
        wrapper.set_my_param(core_constants.REPORT_ID, report_id)
        if wrapper.my_param_is_null(core_constants.DEFAULT_SAMPLE_INFO):
            info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            try:
                patient_id_key = core_constants.PATIENT_STUDY_ID
                wrapper.set_my_param(patient_id_key, info[patient_id_key])
                wrapper.set_my_param(core_constants.DONOR, info[core_constants.ROOT_SAMPLE_NAME])
                wrapper.set_my_param(self.BLOOD_SAMPLE_ID, info[core_constants.NORMAL_ID])
                wrapper.set_my_param(self.TUMOUR_SAMPLE_ID, info[core_constants.TUMOUR_ID])
            except KeyError as err:
                msg = "ID not found in sample info {0}: {1}".format(info, err)
                self.logger.error(msg)
                raise DjerbaPluginError(msg) from err
            if wrapper.my_param_is_null(self.ASSAY):
                # look up the long assay name
                assay_short_name = wrapper.get_my_string(self.ASSAY_SHORT_NAME)
                assay = self.ASSAY_LOOKUP.get(assay_short_name)
                if assay == None:
                    msg = "Assay short name '{0}' not found in lookup table {1}".format(
                        assay_short_name, self.ASSAY_LOOKUP
                    )
                    self.logger.error(msg)
                    raise DjerbaPluginError(msg)
                else:
                    self.logger.debug("Found assay name in lookup table")
                    wrapper.set_my_param(self.ASSAY, assay)
            else:
                self.logger.debug("Using user-configured assay name; short name will be ignored")
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        # populate results directly from config
        results_keys = [
            self.ASSAY,
            self.PRIMARY_CANCER,
            self.SAMPLE_ANATOMICAL_SITE,
            core_constants.DONOR,
            core_constants.PATIENT_STUDY_ID,
            self.TUMOUR_SAMPLE_ID,
            self.BLOOD_SAMPLE_ID,
            core_constants.REPORT_ID,
            self.REQ_APPROVED_DATE,
            self.STUDY
        ]
        results = {k: wrapper.get_my_string(k) for k in results_keys}
        data[core_constants.RESULTS] = results
        return data

    def specify_params(self):
        discovered = [
            self.ASSAY,
            core_constants.DONOR,
            core_constants.REPORT_ID,
            core_constants.PATIENT_STUDY_ID,
            self.BLOOD_SAMPLE_ID,
            self.TUMOUR_SAMPLE_ID,
            core_constants.DEFAULT_SAMPLE_INFO
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        required = [
            self.PRIMARY_CANCER,
            self.SAMPLE_ANATOMICAL_SITE,
            self.REQ_APPROVED_DATE,
            self.STUDY
        ]
        for key in required:
            self.add_ini_required(key)
        self.set_ini_default(self.ASSAY_SHORT_NAME, 'WGTS')
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(core_constants.DEPENDS_CONFIGURE, 'provenance_helper')
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default('render_priority', 10)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

