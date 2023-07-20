"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
import json

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
import djerba.plugins.pwgs.analysis.plugin as analysis
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class main(plugin_base):

    SNV_COUNT_SUFFIX = 'SNP.count.txt'
    RESULTS_SUFFIX = '.mrdetect.txt'
    BAMQC_SUFFIX = 'bamQC_results.json'
    DEFAULT_CONFIG_PRIORITY = 100

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.add_ini_required('primary_snv_count_file')
        
        # Setting default parametersn
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)
        
        # Setting required parameters
        self.add_ini_required('wgs_json')
        
        # Setting default parameters for plugin
        """ Note: these are found after full specification and are not required in the initial config."""
        self.set_ini_default('bamqc_results', None)
        self.set_ini_default('results_file', None)
        self.set_ini_default('primary_snv_count_file', None)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_priorities(self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        tumour_id = config['core'][constants.GROUP_ID]
        qc_dict = self.fetch_coverage_etl_data(tumour_id)
        insert_size_dist_file = self.preprocess_bamqc(config[self.identifier][constants.BAMQC])
        snv_count = self.preprocess_snv_count(config[self.identifier][constants.SNV_COUNT_FILE])
        results_file = config[self.identifier][constants.RESULTS_FILE]
        mrdetect_results = pwgs_tools.preprocess_results(self, results_file)
        if mrdetect_results['outcome'] == "DETECTED":
            ctdna_detection = "Detected"
        elif mrdetect_results['outcome'] == "UNDETECTED":
            ctdna_detection = "Undetected"
        else:
            ctdna_detection = None
            self.logger.info("PWGS SAMPLE: ctDNA inconclusive")
        self.plot_insert_size(insert_size_dist_file, 
                             output_dir = self.workspace.print_location())
        patient_data = self.preprocess_wgs_json(config[self.identifier][constants.WGS_JSON])
        self.logger.info("PWGS SAMPLE: All data found")
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {
            },
            'results': {
                'primary_cancer': patient_data['Primary cancer'],
                'requisition_approved': config['core'][constants.REQ_APPROVED],
                'donor': config['core']['root_sample_name'],
                'group_id': config['core'][constants.GROUP_ID],
                'pwgs_report_id': "_".join((config['core'][constants.GROUP_ID],"v1")),
                'wgs_report_id': patient_data['Report ID'],
                'Patient Study ID': patient_data[constants.PATIENT_ID],
                'study_title': config['core'][constants.STUDY],
                'assay': "plasma Whole Genome Sequencing (pWGS) - 30X (v1.0)",
                'outcome': mrdetect_results['outcome'],
                'median_insert_size': qc_dict['insertSize'],
                'coverage': qc_dict['coverage'],
                'primary_snv_count': snv_count,
                'ctdna_detection': ctdna_detection
            },
            'version': "1.0"
        }
        return data

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

    def plot_insert_size(self, is_path, output_dir ):
        args = [
            os.path.join(constants.RSCRIPTS_LOCATION,'IS.plot.R'),
            '--insert_size_file', is_path,
            '--output_directory', output_dir 
        ]
        subprocess_runner().run(args)
    
    def preprocess_bamqc(self, bamqc_file):
        if bamqc_file == 'None':
            provenance = pwgs_tools.subset_provenance(self, "dnaSeqQC")
            try:
                bamqc_file = pwgs_tools.parse_file_path(self, self.BAMQC_SUFFIX, provenance)
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
    
    def preprocess_snv_count(self, snv_count_path):
        """
        pull SNV count from file
        """
        if snv_count_path == 'None':
            provenance = pwgs_tools.subset_provenance(self, "mrdetect")
            try:    
                snv_count_path = pwgs_tools.parse_file_path(self, self.SNV_COUNT_SUFFIX, provenance)
            except OSError as err:
                msg = "File from workflow {0} with extension {1} was not found in Provenance subset file '{2}' not found".format("mrdetect", self.SNV_COUNT_SUFFIX, constants.PROVENANCE_OUTPUT)
                raise RuntimeError(msg) from err
        with open(snv_count_path, 'r') as hbc_file:
            reader_file = csv.reader(hbc_file, delimiter="\t")
            for row in reader_file:
                try: 
                    snv_count = row[0]
                except IndexError as err:
                    msg = "Incorrect number of columns in SNV Count file: '{0}'".format(snv_count_path)
                    raise RuntimeError(msg) from err
        return int(snv_count)
    
    def preprocess_wgs_json(self, wgs_json):
        with open(wgs_json, 'r') as wgs_results:
            data = json.load(wgs_results)
        patient_data = data["report"]["patient_info"]
        return(patient_data)

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

class MissingQCETLError(Exception):
    pass 
