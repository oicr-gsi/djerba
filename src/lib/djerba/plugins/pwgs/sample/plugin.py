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

    def __init__(self, workspace, identifier, log_level=logging.INFO, log_path=None):
        super().__init__(workspace, identifier, log_level, log_path)
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)

    def configure(self, config):
        config = self.apply_defaults(config)
        config = self.set_all_priorities(config, self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        try:
            self.provenance = analysis.main(self.workspace, self.identifier).subset_provenance("mrdetect")
            snv_count_file = analysis.main(self, self.identifier).parse_file_path(self.SNV_COUNT_SUFFIX, self.provenance)
            results_file = analysis.main(self, self.identifier).parse_file_path(self.RESULTS_SUFFIX, self.provenance)
        except OSError:
            snv_count_file = config[self.identifier][constants.SNV_COUNT_FILE]
            results_file = config[self.identifier][constants.RESULTS_FILE]
            self.logger.info("PWGS SAMPLE: Results file pulled from ini")
        try:
            self.provenance = analysis.main(self.workspace, self.identifier).subset_provenance("dnaSeqQC")
            bamqc_file = analysis.main(self, self.identifier).parse_file_path(self.BAMQC_SUFFIX, self.provenance)
        except OSError:
            bamqc_file = config[self.identifier][constants.BAMQC]
            self.logger.info("PWGS SAMPLE: BAMQC json pulled from ini")
        tumour_id = config['core'][constants.GROUP_ID]
        qc_dict = self.fetch_coverage_etl_data(tumour_id)
        snv_count = self.preprocess_snv_count(snv_count_file)
        insert_size_dist_file = self.preprocess_bamqc(bamqc_file)
        mrdetect_results = analysis.main(self.workspace, self.identifier).preprocess_results(results_file)
        if mrdetect_results['outcome'] == "POSITIVE":
            ctdna_detection = "Detected"
        elif mrdetect_results['outcome'] == "NEGATIVE":
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
            'priorities': self.get_my_priorities(config),
            'attributes': self.get_my_attributes(config),
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

    def preprocess_bamqc(self, bamqc_file):
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
    
    def preprocess_wgs_json(self, wgs_json):
        with open(wgs_json, 'r') as wgs_results:
            data = json.load(wgs_results)
        patient_data = data["report"]["patient_info"]
        return(patient_data)

    def plot_insert_size(self, is_path, output_dir ):
        args = [
            os.path.join(constants.RSCRIPTS_LOCATION,'IS.plot.R'),
            '--insert_size_file', is_path,
            '--output_directory', output_dir 
        ]
        subprocess_runner().run(args)


class MissingQCETLError(Exception):
    pass 
