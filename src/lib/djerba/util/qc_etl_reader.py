"""Read data from QC-ETL; based on `pull_qc` class from Djerba classic"""

import logging

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError as err:
    raise ImportError('Error Importing QC-ETL, try checking python versions') from err


class qc_etl_reader(logger):

    DEFAULT_PINERY_URL = 'http://pinery.gsi.oicr.on.ca'
    DEFAULT_QCETL_CACHE = '/scratch2/groups/gsi/production/qcetl_v1'
    DEFAULT_CBIO_PATH = '/.mounts/labs/CGI/spb-seqware-production/shesmu/common/'+\
        'tgl_project.jsonconfig' # TODO spb-seqware-production is obsolete; update this
    
    class Requisition():
        def __init__(self, pinery_requisition, pinery_assay):
            self.id: int = pinery_requisition['id']
            self.name: str = pinery_requisition['name']
            self.assay: str = pinery_assay['name']
            self.assay_id: int = pinery_assay['id']
            self.assay_description: str = pinery_assay['description']
            self.assay_version: str = pinery_assay['version']

    def __init__(self, pinery_url=None, qcetl_cache=None, cbio_path=None,
                 log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.pinery_url = pinery_url if pinery_url else self.DEFAULT_PINERY_URL
        self.qcetl_cache = qcetl_cache if qcetl_cache else self.DEFAULT_QCETL_CACHE
        self.cbio_path = cbio_path if cbio_path else self.DEFAULT_CBIO_PATH
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

    def fetch_cbio_name(self, project_id):
        with open(self.cbio_path) as in_file:
            data = json.loads(in_file.read())
        try:
            cbioportal_project_id = data['values'][project_id]['cbioportal_project']
            self.logger.debug("Found cbio study ID {0}".format(cbio_project_id))
        except KeyError:
            msg = "Could not find cbio study ID for project {0}".format(project_id)+\
                " in cbio file {0}".format(self.cbio_path)
            self.logger.debug(msg)
            cbioportal_project_id = None
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
