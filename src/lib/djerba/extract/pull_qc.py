#!/usr/bin/env python3

import json
import logging
import urllib.request as request
from djerba.util.logger import logger
import djerba.util.ini_fields as ini
import djerba.util.constants as constants

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class pull_qc(logger):

    class Requisition():
        def __init__(self, pinery_requisition, pinery_assay):
            self.id: int = pinery_requisition['id']
            self.name: str = pinery_requisition['name']
            self.assay: str = pinery_assay['name']
            self.assay_id: int = pinery_assay['id']
            self.assay_description: str = pinery_assay['description']
            self.assay_version: str = pinery_assay['version']

    def __init__(self, config, log_level=logging.WARNING, log_path=None):
        self.config = config
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.pinery_url = self.config[ini.SETTINGS][ini.PINERY_URL]
        self.qcetl_cache = self.config[ini.SETTINGS][ini.QCETL_CACHE]

    def fetch_callability_etl_data(self,tumour_id):
        etl_cache = QCETLCache(self.qcetl_cache)
        callability = etl_cache.mutectcallability.mutectcallability
        columns = gsiqcetl.column.MutetctCallabilityColumn
        callability_select = [
            columns.Donor, 
            columns.TissueType, 
            columns.GroupID,  
            columns.Callability,
        ]
        data = callability.loc[
            (callability[columns.GroupID] == tumour_id),
            callability_select]
        if len(data) > 0:
            callability_val = round(data.iloc[0][columns.Callability].item() * 100,1)
            return(callability_val)
        else:
            msg = "Djerba couldn't find the callability associated with tumour_id {0} in QC-ETL. ".format(tumour_id)
            raise RuntimeError(msg)

    def fetch_coverage_etl_data(self,tumour_id):
        etl_cache = QCETLCache(self.qcetl_cache)
        coverage = etl_cache.bamqc4merged.bamqc4merged
        cov_columns = gsiqcetl.column.BamQc4MergedColumn
        cov_select = [
            cov_columns.Donor, 
            cov_columns.TissueType,
            cov_columns.GroupID, 
            cov_columns.CoverageDeduplicated
        ]
        data = coverage.loc[
            (coverage[cov_columns.GroupID] == tumour_id),
            cov_select]
        if len(data) > 0:
            coverage_value = round(data.iloc[0][cov_columns.CoverageDeduplicated].item(),1)
            return(coverage_value)
        else:
            msg = "Djerba couldn't find the coverage associated with tumour_id {0} in QC-ETL. ".format(tumour_id)
            

    def fetch_pinery_assay(self,requisition_name: str):
        pinery_requisition = self.pinery_get(f'/requisition?name={requisition_name}')
        pinery_assay = self.pinery_get(f'/assay/{pinery_requisition["assay_id"]}')
        requisition = self.Requisition(pinery_requisition, pinery_assay)
        if (requisition.assay == "WGTS - 80XT/30XN") | (requisition.assay == "WGS - 80XT/30XN") :
            requisition_target = 80
        else:
            requisition_target = 40
        return(requisition_target)

    def pinery_get(self,relative_url: str) -> dict:
        if not relative_url.startswith('/'):
            raise RuntimeError('Invalid relative url')
        return json.load(request.urlopen(f'{self.pinery_url}{relative_url}'))
    
