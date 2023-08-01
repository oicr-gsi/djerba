"""Simple Djerba plugin for demonstration and testing: Example 1"""

ipmort json
import logging
from djerba.plugins.base import plugin_base
from djerba.util.logger report logger
import djerba.core.constants as core_constants

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError as err:
    raise ImportError('Error Importing QC-ETL, try checking python versions') from err


class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '1.0.0'

    # default values; from defaults.ini in classic Djerba
    DEFAULT_CBIO_STUDIES_PATH = '/.mounts/labs/CGI/spb-seqware-production/shesmu/common/'+\
        'tgl_project.jsonconfig'
    DEFAULT_PINERY_URL = 'http://pinery.gsi.oicr.on.ca'
    DEFAULT_QCETL_CACHE = '/scratch2/groups/gsi/production/qcetl_v1'

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
            "Project": PLACEHOLDER,
            "Tumour Sample ID": PLACEHOLDER
        },

    """

    def configure(self, config):
        config = self.apply_defaults(config)
        
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.VERSION)
        results = {

        }
        data['results'] = results
        return data

    def render(self, data):
        return "<h3>TODO patient info plugin output goes here</h3>"

    def specify_params(self):
        self.add_ini_required(self.REQUISITION_ID)
        null_default_params = [
            self.ASSAY,
            self.CBIO_STUDY_ID, # defaults to project ID
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

class qc_etl_reader(logger):

    """
    Read data from QC-ETL; based on `pull_qc` class from Djerba classic
    """
    
    class Requisition():
        def __init__(self, pinery_requisition, pinery_assay):
            self.id: int = pinery_requisition['id']
            self.name: str = pinery_requisition['name']
            self.assay: str = pinery_assay['name']
            self.assay_id: int = pinery_assay['id']
            self.assay_description: str = pinery_assay['description']
            self.assay_version: str = pinery_assay['version']

    def __init__(self, config_wrapper, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.pinery_url = config_wrapper.get_my_param(self.PINERY_URL)
        self.cbio_path = config_wrapper.get_my_param(self.CBIO_PROJECT_PATH)
        path_validator(log_level, log_path).validate_input_file(self.cbio_path)
        self.etl_cache = QCETLCache(config_wrapper.get_my_param(self.QCETL_CACHE))

    def fetch_callability_etl_data(self, tumour_id):
        cached_callabilities = self.etl_cache.mutectcallability.mutectcallability
        columns_of_interest = gsiqcetl.column.MutetctCallabilityColumn
        data = cached_callabilities.loc[
            (cached_callabilities[columns_of_interest.GroupID] == tumour_id),
            [columns_of_interest.GroupID, columns_of_interest.Callability]
            ]
        if len(data) > 0:
            callability = round(data.iloc[0][columns_of_interest.Callability].item() * 100,1)
            return callability
        else:
            msg = "Djerba couldn't find the callability associated with "+\
                "tumour_id {0} in QC-ETL. ".format(tumour_id)
            self.logger.debug(msg)
            raise MissingQCETLError(msg)
        
    def fetch_cbio_name(self,project_id):
        with open(self.cbio_path) as in_file:
            data = json.loads(in_file.read())
        cbioportal_project_id = data['values'][project_id]['cbioportal_project']
        return cbioportal_project_id
        
    def fetch_coverage_etl_data(self,tumour_id):
        cached_coverages = self.etl_cache.bamqc4merged.bamqc4merged
        columns_of_interest = gsiqcetl.column.BamQc4MergedColumn
        data = cached_coverages.loc[
            (cached_coverages[columns_of_interest.GroupID] == tumour_id),
            [columns_of_interest.GroupID, columns_of_interest.CoverageDeduplicated]
            ]
        if len(data) > 0:
            coverage_value = \
                round(data.iloc[0][columns_of_interest.CoverageDeduplicated].item(),1)
            return(coverage_value)
        else:
            msg = "Djerba couldn't find the coverage associated with "+\
                "tumour_id {0} in QC-ETL. ".format(tumour_id)
            self.logger.debug(msg)
            raise MissingQCETLError(msg)

    def fetch_pinery_assay(self,requisition_name: str):
        try:
            pinery_requisition = self.pinery_get(f'/requisition?name={requisition_name}')
        except HTTPError:
            msg = "Djerba couldn't find the assay associated with "+\
                "requisition {0} in Pinery. ".format(requisition_name)
            self.logger.debug(msg)
            raise MissingPineryError(msg)
        if len(pinery_requisition) > 0:
            try:
                pinery_assay = self.pinery_get(f'/assay/{pinery_requisition["assay_id"]}')
            except KeyError:
                msg = "Djerba couldn't find an assay type associated with "+\
                    "requisition {0} in Pinery. ".format(requisition_name)
                self.logger.debug(msg)
                raise UnsupportedAssayError(msg)
            requisition = self.Requisition(pinery_requisition, pinery_assay)
            if (requisition.assay == "WGTS - 80XT/30XN") | \
               (requisition.assay == "WGS - 80XT/30XN") :
                requisition_target = 80
            elif (requisition.assay == "WGTS - 40XT/30XN") | \
                 (requisition.assay == "WGS - 40XT/30XN"):
                requisition_target = 40
            else:
                msg = "The assay {0} associated with ".format(requisition.assay)+\
                "requisition {0} in Pinery ".format(requisition_name)+\
                "is not clinically supported."
                self.logger.debug(msg)
                raise UnsupportedAssayError(msg)
            return(requisition_target)
        else:
            msg = "Djerba couldn't find the assay associated with "+\
                "requisition {0} in Pinery. ".format(requisition_name)
            self.logger.debug(msg)
            raise MissingPineryError(msg)

    def pinery_get(self,relative_url: str) -> dict:
        if not relative_url.startswith('/'):
            raise RuntimeError('Invalid relative url')
        return json.load(request.urlopen(f'{self.pinery_url}{relative_url}'))

class MissingQCETLError(Exception):
    pass 

class MissingPineryError(Exception):
    pass

class UnsupportedAssayError(Exception):
    pass
