"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
import json

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as pc
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools
from djerba.util.render_mako import mako_renderer

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class main(plugin_base):

    PRIORITY = 100
    PLUGIN_VERSION = '1.1'
    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        group_id = config[self.identifier][pc.GROUP_ID]
        qc_dict = self.fetch_coverage_etl_data(group_id, config)
        if wrapper.my_param_is_null(pc.INSERT_SIZE):
            wrapper.set_my_param(pc.INSERT_SIZE, int(qc_dict[pc.INSERT_SIZE]))
        if wrapper.my_param_is_null(pc.COVERAGE):
            wrapper.set_my_param(pc.COVERAGE, float(qc_dict[pc.COVERAGE]))
        if wrapper.my_param_is_null(pc.BAMQC):
            wrapper.set_my_param(pc.BAMQC, pwgs_tools.subset_provenance(self, "dnaSeqQC", group_id, pc.BAMQC_SUFFIX))
        if wrapper.my_param_is_null(pc.SNV_COUNT):
            wrapper.set_my_param(pc.SNV_COUNT,  self.preprocess_snv_count(group_id))
        if wrapper.my_param_is_null(pc.RESULTS_FILE):
            wrapper.set_my_param(pc.RESULTS_FILE, pwgs_tools.subset_provenance(self, "mrdetect", group_id, pc.RESULTS_SUFFIX))
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        mrdetect_results = pwgs_tools.preprocess_results(self, config[self.identifier][pc.RESULTS_FILE])
        if mrdetect_results[pc.CTDNA_OUTCOME] == "DETECTED":
            ctdna_detection = "Detected"
        elif mrdetect_results[pc.CTDNA_OUTCOME] == "UNDETECTED":
            ctdna_detection = "Undetected"
        else:
            ctdna_detection = None
            self.logger.info("PWGS SAMPLE: ctDNA inconclusive")
        self.plot_insert_size(self.preprocess_bamqc(config[self.identifier][pc.BAMQC]), 
                                output_dir = self.workspace.print_location())
        patient_data = self.preprocess_wgs_json(config[self.identifier][pc.WGS_JSON])
        self.logger.info("PWGS SAMPLE: All data extracted")
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        results =  {
                pc.REQ_APPROVED: config[self.identifier][pc.REQ_APPROVED],
                pc.CTDNA_OUTCOME: mrdetect_results[pc.CTDNA_OUTCOME],
                pc.INSERT_SIZE: int(config[self.identifier][pc.INSERT_SIZE]),
                pc.COVERAGE: float(config[self.identifier][pc.COVERAGE]),
                pc.SNV_COUNT: int(config[self.identifier][pc.SNV_COUNT]),
                pc.GROUP_ID: config[self.identifier][pc.GROUP_ID],
                'assay': "plasma Whole Genome Sequencing (pWGS) - 30X (v1.0)",
                'primary_cancer': patient_data['Primary cancer'],
                'donor': patient_data['Patient LIMS ID'],
                'wgs_report_id': patient_data['Report ID'],
                'Patient Study ID': patient_data[pc.PATIENT_ID],
                'study_title':  config[self.identifier]['study_id'],
                'pwgs_report_id': "-".join((config[self.identifier][pc.GROUP_ID],"".join(("v",config['core']['report_version'])))),
                'ctdna_detection': ctdna_detection
            }
        data[pc.RESULTS] = results
        return data

    def fetch_coverage_etl_data(self, group_id, config):
        '''fetch median insert size and coverage QC metrics from QC-ETL'''
        self.etl_cache = QCETLCache(self.QCETL_CACHE)
        cached_coverages = self.etl_cache.bamqc4merged.bamqc4merged
        columns_of_interest = gsiqcetl.column.BamQc4MergedColumn
        data = cached_coverages.loc[
            (cached_coverages[columns_of_interest.GroupID] == group_id),
            [columns_of_interest.GroupID, columns_of_interest.CoverageDeduplicated, columns_of_interest.InsertMedian]
            ]
        qc_dict = {}
        if len(data) > 0:
           qc_dict[pc.COVERAGE] = round(data.iloc[0][columns_of_interest.CoverageDeduplicated].item(),1)
           qc_dict[pc.INSERT_SIZE] = round(data.iloc[0][columns_of_interest.InsertMedian].item(),1)
        else:
            coverage = config[self.identifier][pc.COVERAGE]
            median_insert_size = config[self.identifier][pc.INSERT_SIZE]
            msg = "QC metrics associated with group_id {0} not found in QC-ETL. Trying to use ini specified parameters instead: cov = {1}, IS = {2}.".format(group_id, coverage, median_insert_size)
            self.logger.debug(msg)
            try:
                qc_dict[pc.COVERAGE] = float(coverage)
            except ValueError:
                msg = "No useful coverage information was found in ini."
                raise ValueError(msg)
            try:
                qc_dict[pc.INSERT_SIZE] = int(median_insert_size)
            except ValueError:
                msg = "No useful insert size information was found in ini."
                raise ValueError(msg)
        return(qc_dict)

    def plot_insert_size(self, is_path, output_dir ):
        '''call R to plot insert size distribution'''
        args = [
            os.path.join(os.path.dirname(__file__),'IS.plot.R'),
            '--insert_size_file', is_path,
            '--output_directory', output_dir 
        ]
        subprocess_runner().run(args)
    
    def preprocess_bamqc(self, bamqc_file):
        '''parse bam-qc json for insert size distribution and return histogram-ready'''        
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
    
    def preprocess_snv_count(self, group_id, snv_count_path = "None" ):
        """
        pull SNV count from file
        """
        if snv_count_path == "None":
            snv_count_path = pwgs_tools.subset_provenance(self, "mrdetect", group_id, pc.SNV_COUNT_SUFFIX)
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
        '''find patient info from WGS/WGTS djerba report json'''
        with open(wgs_json, 'r') as wgs_results:
            data = json.load(wgs_results)
        patient_data = data["report"]["patient_info"]
        return(patient_data)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.SAMPLE_TEMPLATE_NAME, data)
    
    def specify_params(self):
        required = [
            pc.REQ_APPROVED,
            pc.GROUP_ID,
            pc.WGS_JSON,
            'study_id'
        ]
        for key in required:
            self.add_ini_required(key)
        discovered = [
            pc.BAMQC,
            pc.RESULTS_FILE,
            pc.SNV_COUNT,
            pc.COVERAGE,
            pc.INSERT_SIZE
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

class MissingQCETLError(Exception):
    pass 

class MissingIniError(Exception):
    pass 
