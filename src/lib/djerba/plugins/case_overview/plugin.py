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
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
import djerba.util.assays as assays


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

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        report_id = wrapper.get_core_string(core_constants.REPORT_ID)
        wrapper.set_my_param(core_constants.REPORT_ID, report_id)
        # Look up assay long name from assay short name
        # use manually configured values if available
        # otherwise, check for JSON file(s):
        # 1) input_params.json
        # - written by input_params_helper or tar_input_params_helper
        # - has general purpose values for all assays
        # - for TAR only, also has sample IDs and patient study ID
        # 2) sample_info.json
        # - written by provenance_helper
        # - for non-TAR reports only, has sample IDs and patient study ID
        input_params = self.workspace.read_maybe_input_params()
        
        id_keys = [
            self.BLOOD_SAMPLE_ID,
            self.TUMOUR_SAMPLE_ID,
            core_constants.PATIENT_STUDY_ID
        ]
        
        if input_params:
            keys = [
                self.PRIMARY_CANCER,
                self.REQUISITION_APPROVED,
                self.SITE_OF_BIOPSY,
                self.DONOR,
                self.STUDY,
                self.ASSAY
            ]
            for key in keys:
                wrapper.set_my_param_if_null(key, input_params[key])
        

        # Now, get assay, for assay related information.
        assay = wrapper.get_my_string(self.ASSAY)

        if assay == assays.TAR:
            if input_params:
                for key in id_keys:
                    wrapper.set_my_param_if_null(key, input_params[key])
       
        if assay!=assays.TAR and self.workspace.has_file(core_constants.DEFAULT_SAMPLE_INFO):
            sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            for key in id_keys:
                # non-TAR uses sample_info.json for ID values
                wrapper.set_my_param_if_null(key, sample_info[key])

        # Look up assay long name from assay short name
        if wrapper.my_param_is_null(self.ASSAY_DESCRIPTION):
            [ok, msg] = assays.name_status(assay)
            if ok:
                self.logger.debug("Found assay name '{0}' in lookup table".format(assay))
                wrapper.set_my_param(self.ASSAY_DESCRIPTION, assays.get_case_overview_description(assay))
            else:
                msg = "Cannot resolve assay description from config or default lookup: "+msg
                self.logger.error(msg)
                raise DjerbaPluginError(msg)


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
            self.REQUISITION_APPROVED
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default('render_priority', 40)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
