"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
from decimal import Decimal

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.logger import logger

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class main(plugin_base):

    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        self.logger.info("PWGS: No extracting necessary")
        tumour_id = self.workspace.read_core_config()['tumour_id']
        qc_dict = self.fetch_coverage_etl_data(tumour_id)
        data = {
            'plugin_name': 'pwgs.sample',
            'clinical': True,
            'failed': False,
            'merge_inputs': {
                'gene_information': []
            },
            'results': {
                'median_insert_size': qc_dict['insertSize'],
                'tumour_fraction': float(config_section[constants.TUMOUR_FRACTION_READS]),
                'coverage': qc_dict['coverage'],
                'primary_snv_count': float(config_section[constants.SNV_COUNT])
            }
        }
        return data

    def render(self, data):
        args = data
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'html'
        ))
        report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
        mako_template = report_lookup.get_template(constants.SAMPLE_TEMPLATE_NAME)
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            raise
        return html    
    
    def fetch_coverage_etl_data(self,tumour_id):
        self.qcetl_cache = "/scratch2/groups/gsi/production/qcetl_v1"
        self.etl_cache = QCETLCache(self.qcetl_cache)
        cached_coverages = self.etl_cache.bamqc4merged.bamqc4merged
        columns_of_interest = gsiqcetl.column.BamQc4MergedColumn
        data = cached_coverages.loc[
            (cached_coverages[columns_of_interest.GroupID] == tumour_id),
            [columns_of_interest.GroupID, columns_of_interest.CoverageDeduplicated, columns_of_interest.InsertMedian]
            ]
        if len(data) > 0:
           qc_dict = {'coverage' : round(data.iloc[0][columns_of_interest.CoverageDeduplicated].item(),1)}
           qc_dict['insertSize'] = round(data.iloc[0][columns_of_interest.InsertMedian].item(),1)
           return(qc_dict)
        else:
            msg = "Djerba couldn't find the QC metrics associated with tumour_id {0} in QC-ETL. ".format(tumour_id)
            self.logger.debug(msg)
            raise MissingQCETLError(msg)
    
class MissingQCETLError(Exception):
    pass 
