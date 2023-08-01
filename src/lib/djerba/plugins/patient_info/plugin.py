"""Plugin to write a table of patient info"""

import json
import logging
from djerba.plugins.base import plugin_base
from djerba.util.logger report logger
from djerba.util.qc_etl_reader import qc_etl_reader
import djerba.core.constants as core_constants


class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '1.0.0'

    # results keys; some previously in djerba.util.constants
    ASSAY = 'ASSAY'
    BLOOD_SAMPLE_ID = 'BLOOD_SAMPLE_ID'
    PATIENT_LIMS_ID = 'PATIENT_LIMS_ID'
    PATIENT_STUDY_ID = 'PATIENT_STUDY_ID'
    PRIMARY_CANCER = 'PRIMARY_CANCER'
    PROJECT = 'PROJECT'
    # REPORT_ID is in core_constants
    REQUISITION_ID = 'REQUISITION_ID'
    REQ_APPROVED_DATE = 'REQ_APPROVED_DATE'
    SAMPLE_ANATOMICAL_SITE = 'SAMPLE_ANATOMICAL_SITE'
    SEX = 'SEX'
    STUDY = 'STUDY'
    TUMOUR_SAMPLE_ID = 'TUMOUR_SAMPLE_ID'

    # additional parameter keys from ini_fields.py in classic Djerba
    PINERY_URL = 'pinery_url'
    QCETL_CACHE = 'qcetl_cache'
    CBIO_PROJECT_PATH = 'cbio_studies_path'
    CBIO_STUDY_ID = 'cbio_study_id' # defaults to project ID

    """
    Populate a data strucutre like this, and render as HTML:
    "patient_info": {
            "Assay": "Whole genome and transcriptome sequencing (WGTS)",
            "Blood Sample ID": PLACEHOLDER,
            "Patient Genetic Sex": PLACEHOLDER,
            "Patient LIMS ID": PLACEHOLDER,
            "Patient Study ID": PLACEHOLDER,
            "Primary cancer": PLACEHOLDER,
            "Report ID": PLACEHOLDER,
            "Requisition ID": PLACEHOLDER,
            "Requisition Approved": 2023/01/01,
            "Site of biopsy/surgery": PLACEHOLDER,
            "Study": PLACEHOLDER,
            "Tumour Sample ID": PLACEHOLDER
        },
    """

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        if wrapper.has_my_param(self.CBIO_STUDY_ID):
            name = wrapper.get_my_string(self.CBIO_STUDY_ID)
            msg = "Using manually configured cBioportal project name {0}".format(name)
            self.logger.debug(msg)
        else:
            reader = qc_etl_reader(log_level=self.log_level, log_path=self.log_path)
            project = wrapper.get_my_string(self.PROJECT)
            cbio_study_id = reader.fetch_cbio_name()
            if cbio_study_id == None:
                msg = "No cBioportal project name found; falling back to "+\
                    "project name {0}".format(project)
                self.logger.warning(msg)
                cbio_study_id = project
            wrapper.set_my_param(self.CBIO_STUDY_ID, cbio_study_id)
        core_project = wrapper.get_my_string(core_constants.CORE, core_constants.PROJECT)
        wrapper.set_my_param(self.PROJECT, core_project)
        report_id = wrapper.get_my_string(core_constants.CORE, core_constants.REPORT_ID)
        wrapper.set_my_param(self.REPORT_ID, report_id)
        donor_id = wrapper.get_my_string(core_constants.CORE, core_constants.DONOR)
        wrapper.set_my_param(self.PATIENT_LIMS_ID, donor_id)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.VERSION)
        results = {}
        for key in [
            self.ASSAY,
            self.CBIO_STUDY_ID, # get from QC-ETL, or default to project ID
            self.BLOOD_SAMPLE_ID, # get from sample info JSON
            self.PATIENT_LIMS_ID, # equal to donor ID
            self.PATIENT_STUDY_ID, # get from sample info JSON
            self.PRIMARY_CANCER, # manually configured
            self.PROJECT, # get from core config
            self.REPORT_ID, # get from core config
            self.REQ_APPROVED_DATE, # manually configured
            self.REQUISITION_ID, # get from core config
            self.SAMPLE_ANATOMICAL_SITE, # manually configured
            self.SEX, # manually configured
            self.STUDY,
            self.TUMOUR_SAMPLE_ID # get from sample info JSON
        ]:
            results[key] = wrapper.get_my_param(key)
        data['results'] = results
        return data

    def render(self, data):
        return "<h3>TODO patient info plugin output goes here</h3>"

    def specify_params(self):
        self.add_ini_required(self.REQUISITION_ID)
        null_default_params = [
            self.ASSAY,
            self.CBIO_STUDY_ID, # get from QC-ETL, or default to project ID
            self.BLOOD_SAMPLE_ID,
            self.PATIENT_LIMS_ID, # equal to donor ID
            self.PATIENT_STUDY_ID,
            self.PRIMARY_CANCER,
            self.PROJECT, # get from core config
            self.REPORT_ID, # get from core config
            self.REQ_APPROVED_DATE,
            self.SAMPLE_ANATOMICAL_SITE,
            self.SEX,
            self.STUDY,
            self.TUMOUR_SAMPLE_ID
        ]
        for param in null_default_params:
            self.set_ini_null_default(param)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)
