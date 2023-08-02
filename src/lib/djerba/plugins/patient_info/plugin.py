"""Plugin to make the 'Case Overview' and 'Sample Information' sections"""

"""
We use most (but not all) of the same parameters as "patient info" JSON in Djerba classic.
Example JSON section from Djerba classic:

        "patient_info": {
            "Assay": "Whole genome and transcriptome sequencing (WGTS)-80X Tumour, 30X Normal (v2.0)",
            "Blood Sample ID": "PLACEHOLDER",
            "Patient Genetic Sex": "Male",
            "Patient LIMS ID": "PLACEHOLDER",
            "Patient Study ID": "PLACEHOLDER",
            "Primary cancer": "Pancreatic Adenocarcinoma",
            "Report ID": "PLACEHOLDER",
            "Requisition ID": "REQ01",
            "Requisition Approved": "2021/01/01",
            "Site of biopsy/surgery": "PLACEHOLDER",
            "Study": "PLACEHOLDER",
            "Project": "PLACEHOLDER",
            "Tumour Sample ID": "PLACEHOLDER"
        },
"""

import logging
from time import strftime
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'patient_info_template.html'

    # config/results keys
    # REPORT_ID, DONOR and STUDY from core
    # Patient LIMS ID = DONOR
    ASSAY_SHORT_NAME = "assay short name"
    ASSAY = "assay"
    BLOOD_SAMPLE_ID = "blood sample id"
    PRIMARY_CANCER = "primary cancer"
    REPORT_DATE = "report date"
    REQUISITION_ID = "requisition id"
    REQ_APPROVED_DATE = "requisition approved"
    SAMPLE_ANATOMICAL_SITE = "site of biopsy/surgery"
    STUDY = "study"
    TUMOUR_SAMPLE_ID = "tumour sample id"

    ASSAY_LOOKUP = {
        'WGTS': 'Whole genome and transcriptome sequencing (WGTS)'+\
        '-80X Tumour, 30X Normal (v3.0)',
    }

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        report_id = wrapper.get_core_string(core_constants.REPORT_ID)
        wrapper.set_my_param(core_constants.REPORT_ID, report_id)
        info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
        try:
            patient_id_key = core_constants.PATIENT_STUDY_ID
            wrapper.set_my_param(patient_id_key, info[patient_id_key])
            wrapper.set_my_param(core_constants.DONOR, info[core_constants.ROOT_SAMPLE_NAME])
            wrapper.set_my_param(core_constants.DONOR, info[core_constants.ROOT_SAMPLE_NAME])
            wrapper.set_my_param(self.BLOOD_SAMPLE_ID, info[core_constants.NORMAL_ID])
            wrapper.set_my_param(self.TUMOUR_SAMPLE_ID, info[core_constants.TUMOUR_ID])
        except KeyError as err:
            msg = "ID not found in sample info {0}: {1}".format(info, err)
            self.logger.error(msg)
            raise DjerbaPluginError(msg) from err
        if wrapper.my_param_is_null(self.REPORT_DATE):
            wrapper.set_my_param(self.REPORT_DATE, strftime("%Y/%m/%d"))
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        # populate results directly from config
        results_keys = [
            self.PRIMARY_CANCER,
            self.SAMPLE_ANATOMICAL_SITE,
            core_constants.DONOR,
            core_constants.PATIENT_STUDY_ID,
            self.TUMOUR_SAMPLE_ID,
            self.BLOOD_SAMPLE_ID,
            core_constants.REPORT_ID,
            self.REPORT_DATE,
            self.REQ_APPROVED_DATE,
            self.STUDY
        ]
        results = {k: wrapper.get_my_string(k) for k in results_keys}
        # look up the long assay name
        assay_short_name = wrapper.get_my_string(self.ASSAY_SHORT_NAME)
        try:
            results[self.ASSAY] = self.ASSAY_LOOKUP[assay_short_name]
        except KeyError as err:
            msg = "Assay short name '{0}' not found in lookup table {1}: {2}".format(
                assay_short_name, self.ASSAY_LOOKUP, err
            )
            self.logger.error(msg)
            raise DjerbaPluginError(msg) from err
        data[core_constants.RESULTS] = results
        return data

    def specify_params(self):
        discovered = [
            self.REPORT_DATE,
            core_constants.DONOR,
            core_constants.REPORT_ID,
            core_constants.PATIENT_STUDY_ID,
            self.BLOOD_SAMPLE_ID,
            self.TUMOUR_SAMPLE_ID,
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        required = [
            self.ASSAY_SHORT_NAME,
            self.PRIMARY_CANCER,
            self.SAMPLE_ANATOMICAL_SITE,
            self.REQ_APPROVED_DATE,
            self.STUDY
        ]
        for key in required:
            self.add_ini_required(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(core_constants.DEPENDS_CONFIGURE, 'provenance_helper')
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
