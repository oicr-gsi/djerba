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
import os

class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'case_overview_template.html'
    INPUT_PARAMS_FILE = 'input_params.json'
    
    # config/results keys
    # REPORT_ID, DONOR and STUDY from core
    # Patient LIMS ID = DONOR
    ASSAY = "assay"
    ASSAY_DESCRIPTION = 'assay_description'
    BLOOD_SAMPLE_ID = "normal_id"
    PRIMARY_CANCER = "primary_cancer"
    REQUISITION_ID = "requisition id"
    REQ_APPROVED_DATE = "requisition_approved"
    SAMPLE_ANATOMICAL_SITE = "site_of_biopsy"
    STUDY = "study"
    DONOR = "donor"
    TUMOUR_SAMPLE_ID = "tumour_id"
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
        
        # Get the working directory
        work_dir = self.workspace.get_work_dir()

        # If input_params.json exists, read it
        input_data_path = os.path.join(work_dir, self.INPUT_PARAMS_FILE)
        if os.path.exists(input_data_path):
            input_data = self.workspace.read_json(self.INPUT_PARAMS_FILE)
        else:
            msg = "Could not find input_params.json"
            #print(msg) <-- TO DO: have logger raise warning

        # Get parameters from input_params.json if not manually specified
        if wrapper.my_param_is_null('primary_cancer'):
            wrapper.set_my_param('primary_cancer', input_data['primary_cancer'])
        if wrapper.my_param_is_null('requisition_approved'):
            wrapper.set_my_param('requisition_approved', input_data['requisition_approved'])
        if wrapper.my_param_is_null('site_of_biopsy'):
            wrapper.set_my_param('site_of_biopsy', input_data['site_of_biopsy'])
        if wrapper.my_param_is_null('donor'):
            wrapper.set_my_param('donor', input_data['donor'])
        if wrapper.my_param_is_null('study'):
            wrapper.set_my_param('study', input_data['study'])
        if wrapper.my_param_is_null('assay'):
            wrapper.set_my_param('assay', input_data['assay'])
        
        # Get assay
        assay = config[self.identifier][self.ASSAY]
        
        # Look up assay long name from assay short name
        if wrapper.my_param_is_null('assay_description'):
            assay_description = self.ASSAY_LOOKUP.get(assay)
            if assay_description == None:
                msg = "Assay short name '{0}' not found in lookup table {1}".format(
                    assay, self.ASSAY_LOOKUP
                )
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
            else:
                self.logger.debug("Found assay name in lookup table")
                wrapper.set_my_param(self.ASSAY_DESCRIPTION, assay_description)

        # Get parameters from default sample info
        if wrapper.my_param_is_null(core_constants.DEFAULT_SAMPLE_INFO) and assay != "TAR":
            info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            try:
                patient_id_key = core_constants.PATIENT_STUDY_ID
                wrapper.set_my_param(patient_id_key, info[patient_id_key])
                wrapper.set_my_param(self.BLOOD_SAMPLE_ID, info[core_constants.NORMAL_ID])
                wrapper.set_my_param(self.TUMOUR_SAMPLE_ID, info[core_constants.TUMOUR_ID])
            except KeyError as err:
                msg = "ID not found in sample info {0}: {1}".format(info, err)
                self.logger.error(msg)
                raise DjerbaPluginError(msg) from err
        # TAR can use normal and tumour ids from input_params_helper
        elif assay == "TAR":
            if wrapper.my_param_is_null(self.BLOOD_SAMPLE_ID):
                wrapper.set_my_param(self.BLOOD_SAMPLE_ID, input_data['normal_id'])
            if wrapper.my_param_is_null(self.TUMOUR_SAMPLE_ID):
                wrapper.set_my_param(self.TUMOUR_SAMPLE_ID, input_data['tumour_id'])
            if wrapper.my_param_is_null(core_constants.PATIENT_STUDY_ID):
                wrapper.set_my_param(core_constants.PATIENT_STUDY_ID, input_data[core_constants.PATIENT_STUDY_ID])

        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        # populate results directly from config
        results_keys = [
            self.ASSAY,
            self.ASSAY_DESCRIPTION,
            self.PRIMARY_CANCER,
            self.SAMPLE_ANATOMICAL_SITE,
            self.DONOR,
            self.STUDY,
            core_constants.PATIENT_STUDY_ID,
            self.TUMOUR_SAMPLE_ID,
            self.BLOOD_SAMPLE_ID,
            core_constants.REPORT_ID,
            self.REQ_APPROVED_DATE,
        ]
        results = {k: wrapper.get_my_string(k) for k in results_keys}
        data[core_constants.RESULTS] = results
        return data

    def specify_params(self):
        discovered = [
            self.ASSAY,
            self.ASSAY_DESCRIPTION,
            self.PRIMARY_CANCER,
            self.SAMPLE_ANATOMICAL_SITE,
            self.DONOR,
            self.STUDY,
            core_constants.PATIENT_STUDY_ID,
            self.TUMOUR_SAMPLE_ID,
            self.BLOOD_SAMPLE_ID,
            core_constants.REPORT_ID,
            self.REQ_APPROVED_DATE,
            core_constants.DEFAULT_SAMPLE_INFO
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(core_constants.DEPENDS_CONFIGURE, 'provenance_helper')
        self.set_ini_default(core_constants.DEFAULT_SAMPLE_INFO, 'None')
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default('render_priority', 10)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

