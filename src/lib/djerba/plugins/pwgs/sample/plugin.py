"""Djerba plugin for pwgs sample reporting"""
import os
import csv

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
import djerba.plugins.pwgs.analysis.plugin as analysis
from djerba.core.workspace import workspace

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class main(plugin_base):

    SNV_COUNT_SUFFIX = 'SNP.count.txt'

    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        tumour_id = self.workspace.read_core_config()['tumour_id']
        qc_dict = self.fetch_coverage_etl_data(tumour_id)
        try:
            self.provenance = analysis.main(self.workspace).subset_provenance()
            snv_count_path = analysis.main(self).parse_file_path(self.SNV_COUNT_SUFFIX, self.provenance)
        except OSError:
            snv_count_path = config_section[constants.SNV_COUNT_FILE]
        snv_count = self.preprocess_snv_count(snv_count_path)
        self.logger.info("PWGS SAMPLE: All data found")
        data = {
            'plugin_name': 'pwgs.sample',
            'clinical': True,
            'failed': False,
            'merge_inputs': {
                'gene_information': []
            },
            'results': {
                'median_insert_size': qc_dict['insertSize'],
                'coverage': qc_dict['coverage'],
                'primary_snv_count': snv_count
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
        
    def preprocess_snv_count(self, snv_count_path):
        """
        pull SNV count from file
        """
        with open(snv_count_path, 'r') as hbc_file:
            reader_file = csv.reader(hbc_file, delimiter="\t")
            for row in reader_file:
                try: 
                    snv_count = row[0]
                except IndexError as err:
                    msg = "Incorrect number of columns in SNV Count file: '{0}'".format(snv_count_path)
                    raise RuntimeError(msg) from err
        return int(snv_count)
    
class MissingQCETLError(Exception):
    pass 
