"""
Plugin to generate the Case Overview report section

Assay can be specified by:
- Short name, which looks up in a table of known assays
- Full name -- if this parameter is set manually, the short name is ignored
Typically the short name will be used, but the full name is supported as an INI parameter
in case assay names are introduced/changed at short notice
"""

import os
import logging
from time import strftime
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
import djerba.util.assays as assays
import djerba.util.input_params_tools as input_params_tools

class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'case_overview_template.html'

    # config/results keys
    # REPORT_ID, DONOR and STUDY from core
    # Patient LIMS ID = DONOR
    ASSAY = "assay"
    ASSAY_DESCRIPTION = 'assay_description'
    BLOOD_SAMPLE_ID = "normal_id"
    PRIMARY_CANCER = "primary_cancer"
    REQUISITION_ID = "requisition id"
    REQUISITION_APPROVED = "requisition_approved"
    SITE_OF_BIOPSY = "site_of_biopsy"
    STUDY = "study"
    DONOR = "donor"
    TUMOUR_SAMPLE_ID = "tumour_id"
    TUMOUR_DEPTH = 80
    NORMAL_DEPTH = 40

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        report_id = wrapper.get_core_string(core_constants.REPORT_ID)
        wrapper.set_my_param(core_constants.REPORT_ID, report_id)
        work_dir = self.workspace.get_work_dir()        
        
        # Get input_data.json if it exists; else return None
        input_data = input_params_tools.get_input_params_json(self)
        if input_data == None:
            msg = "Input_params.json does not exist. Parameters must be set manually."
            self.logger.warning(msg)

        # Get parameters from input_params.json if not manually specified
        if wrapper.my_param_is_null(self.PRIMARY_CANCER):
            wrapper.set_my_param(self.PRIMARY_CANCER, input_data[self.PRIMARY_CANCER])
        if wrapper.my_param_is_null(self.REQUISITION_APPROVED):
            wrapper.set_my_param(self.REQUISITION_APPROVED, input_data[self.REQUISITION_APPROVED])
        if wrapper.my_param_is_null(self.SITE_OF_BIOPSY):
            wrapper.set_my_param(self.SITE_OF_BIOPSY, input_data[self.SITE_OF_BIOPSY])
        if wrapper.my_param_is_null(self.DONOR):
            wrapper.set_my_param(self.DONOR, input_data[self.DONOR])
        if wrapper.my_param_is_null(self.STUDY):
            wrapper.set_my_param(self.STUDY, input_data[self.STUDY])
        if wrapper.my_param_is_null(self.ASSAY):
            wrapper.set_my_param(self.ASSAY, input_data[self.ASSAY])
        
        # Get assay
        assay = wrapper.get_my_string(self.ASSAY)
        # Look up assay long name from assay short name
        if wrapper.my_param_is_null(self.ASSAY_DESCRIPTION):
            [ok, msg] = assays.name_status(assay)
            if ok:
                self.logger.debug("Found assay name '{0}' in lookup table".format(assay))
                wrapper.set_my_param(self.ASSAY_DESCRIPTION, assays.get_description(assay))
            else:
                msg = "Cannot resolve assay description from config or default lookup: "+msg
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        # Get parameters from default sample info
        if wrapper.my_param_is_null(core_constants.DEFAULT_SAMPLE_INFO) and assay != "TAR":
            wrapper.set_my_param(core_constants.DEFAULT_SAMPLE_INFO, os.path.join(work_dir, core_constants.DEFAULT_SAMPLE_INFO))
            info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            try:
                wrapper.set_my_param(core_constants.PATIENT_STUDY_ID, info[core_constants.PATIENT_STUDY_ID])
                wrapper.set_my_param(self.BLOOD_SAMPLE_ID, info[core_constants.NORMAL_ID])
                wrapper.set_my_param(self.TUMOUR_SAMPLE_ID, info[core_constants.TUMOUR_ID])
            except KeyError as err:
                msg = "ID not found in sample info {0}: {1}".format(info, err)
                self.logger.error(msg)
                raise DjerbaPluginError(msg) from err
        # TAR can use normal and tumour ids from input_params_helper
        elif assay == "TAR":
            if wrapper.my_param_is_null(core_constants.DEFAULT_SAMPLE_INFO):
                wrapper.set_my_param(core_constants.DEFAULT_SAMPLE_INFO, "None")
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
            self.SITE_OF_BIOPSY,
            self.DONOR,
            self.STUDY,
            core_constants.PATIENT_STUDY_ID,
            self.TUMOUR_SAMPLE_ID,
            self.BLOOD_SAMPLE_ID,
            core_constants.REPORT_ID,
            self.REQUISITION_APPROVED,
        ]
        results = {k: wrapper.get_my_string(k) for k in results_keys}
        data[core_constants.RESULTS] = results
        return data

    def specify_params(self):
        discovered = [
            self.ASSAY,
            self.ASSAY_DESCRIPTION,
            self.PRIMARY_CANCER,
            self.SITE_OF_BIOPSY,
            self.DONOR,
            self.STUDY,
            core_constants.PATIENT_STUDY_ID,
            self.TUMOUR_SAMPLE_ID,
            self.BLOOD_SAMPLE_ID,
            core_constants.REPORT_ID,
            self.REQUISITION_APPROVED,
            core_constants.DEFAULT_SAMPLE_INFO
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(core_constants.DEPENDS_CONFIGURE, 'provenance_helper')
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default('render_priority', 10)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
