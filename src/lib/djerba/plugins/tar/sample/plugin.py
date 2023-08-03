"""
Djerba plugin for pwgs sample reporting
AUTHOR: Felix Beaudry
"""
import os
import csv
import logging
import json

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.tar.sample.constants as constants
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class main(plugin_base):

    PLUGIN_VERSION = '1.0.0'
    DEFAULT_CONFIG_PRIORITY = 100

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        


    def specify_params(self):
        #self.add_ini_required('primary_snv_count_file')
        
        # Setting priorities
        self.set_priority_defaults(self.DEFAULT_CONFIG_PRIORITY)

        # Setting default parameters
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)
        self.set_ini_default('attributes', 'clinical')

        # I removed these from core and temporarily added them to [tar.sample]:
        self.add_ini_required('group_id')
        self.add_ini_required('root_sample_name')
        self.add_ini_required('study_title')

        # Setting required parameters
        self.add_ini_required('oncotree')
        self.add_ini_required('known_variants')
        self.add_ini_required('cancer_content')
        self.add_ini_required('raw_coverage')
        self.add_ini_required('unique_coverage')

        # Setting default parameters for plugin
        """ Note: these are found after full specification and are not required in the initial config."""
        # self.set_ini_default('bamqc_results', None)
        # self.set_ini_default('results_file', None)
        # self.set_ini_default('primary_snv_count_file', None)

    def configure(self, config):
        config = self.apply_defaults(config)
        #wrapper = self.get_config_wrapper(config)
        #wrapper.set_my_priorities(self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        # tumour_id = config['core'][constants.GROUP_ID]
        # qc_dict = self.fetch_coverage_etl_data(tumour_id)
        # insert_size_dist_file = self.preprocess_bamqc(config[self.identifier][constants.BAMQC])
        self.logger.info("TAR SAMPLE: All data found")
        data = {
            'plugin_name': self.identifier+' plugin',
            'version': self.PLUGIN_VERSION,
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {
            },
            'results': {
                 
                # NOTE: thes three used to say "core" but got changed to "self.identifier"

                'group_id': config[self.identifier][constants.GROUP_ID],
                'root_sample_name': config[self.identifier][constants.DONOR],
                'study_title': config[self.identifier][constants.STUDY],
                

                'oncotree': config[self.identifier][constants.ONCOTREE],
                "known_variants" : config[self.identifier][constants.KNOWN_VARIANTS],
                "cancer_content" : float(config[self.identifier][constants.CANCER_CONTENT]),
                "raw_coverage" : int(config[self.identifier][constants.RAW_COVERAGE]),
                "unique_coverage" : int(config[self.identifier][constants.UNIQUE_COVERAGE])
            }
        }
        self.fetch_coverage_etl_data(config[self.identifier][constants.GROUP_ID], config)
        return data

    def fetch_coverage_etl_data(self, group_id, config):
        self.qcetl_cache = "/scratch2/groups/gsi/production/qcetl_v1"
        self.etl_cache = QCETLCache(self.qcetl_cache)
        cached_coverages = self.etl_cache.bamqc4merged.bamqc4merged
        columns_of_interest = gsiqcetl.column.BamQc4MergedColumn
        data = cached_coverages.loc[
            (cached_coverages[columns_of_interest.GroupID] == group_id),
            [columns_of_interest.GroupID, columns_of_interest.CoverageDeduplicated, columns_of_interest.InsertMedian]
            ]
        qc_dict = {}
        if len(data) > 0:
           qc_dict['coverage'] = round(data.iloc[0][columns_of_interest.CoverageDeduplicated].item(),1)
           qc_dict['insertSize'] = round(data.iloc[0][columns_of_interest.InsertMedian].item(),1)
        else:
            coverage = config[self.identifier]['coverage']
            median_insert_size = config[self.identifier]['median_insert_size']
            msg = "QC metrics associated with group_id {0} not found in QC-ETL. Trying to use ini specified parameters instead: cov = {1}, IS = {2}.".format(group_id, coverage, median_insert_size)
            self.logger.debug(msg)
            try:
                qc_dict['coverage'] = float(coverage)
            except ValueError:
                msg = "No useful coverage information was found in ini."
                raise ValueError(msg)
            try:
                qc_dict['insertSize'] = int(median_insert_size)
            except ValueError:
                msg = "No useful insert size information was found in ini."
                raise ValueError(msg)
        return(qc_dict)

    def preprocess_bamqc(self, bamqc_file):
        if bamqc_file == 'None':
            provenance = analysis.main(self.workspace, self.identifier).subset_provenance("dnaSeqQC")
            try:
                bamqc_file = analysis.main(self, self.identifier).parse_file_path(self.BAMQC_SUFFIX, provenance)
            except OSError as err:
                msg = "File from workflow {0} with extension {1} was not found in Provenance subset file '{2}' not found".format("dnaSeqQC", self.BAMQC_SUFFIX,constants.PROVENANCE_OUTPUT)
                raise RuntimeError(msg) from err
        output_dir = self.workspace.print_location()
        with open(bamqc_file, 'r') as bamqc_results:
            data = json.load(bamqc_results)
        is_data = data['insert size histogram']
        file_location = os.path.join(output_dir, 'insert_size_distribution.csv')
        with open(file_location,'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['size','count'])
            for i in is_data:
                csv_out.writerow([i,is_data[i]])
        return(file_location)

    def render(self, data):
        args = data
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
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

class MissingQCETLError(Exception):
    pass 
