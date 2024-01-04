"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
import json
import requests

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

    PRIORITY = 160
    PLUGIN_VERSION = '1.2'
    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)

        qc_metrics =[
                pc.INSERT_SIZE,
                pc.COVERAGE 
            ]
        for metric in qc_metrics:
            wrapper = self.fill_qc_if_null(wrapper, config, metric)

        wrapper = self.fill_file_if_null(wrapper, pc.SNV_COUNT, pc.SNV_COUNT_SUFFIX)
        wrapper = self.fill_file_if_null(wrapper, pc.BAMQC, pc.BAMQC_SUFFIX)
        wrapper = self.fill_file_if_null(wrapper, pc.RESULTS_FILE, pc.RESULTS_SUFFIX)

        return wrapper.get_config()

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
        self.logger.info("PWGS SAMPLE: All data extracted")
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        results =  {
                pc.INSERT_SIZE: int(config[self.identifier][pc.INSERT_SIZE]),
                pc.COVERAGE: float(config[self.identifier][pc.COVERAGE]),
                pc.SNV_COUNT: int(self.preprocess_snv_count(config[self.identifier][pc.SNV_COUNT])),
                pc.CTDNA_OUTCOME: mrdetect_results[pc.CTDNA_OUTCOME],
                'ctdna_detection': ctdna_detection
            }
        data[pc.RESULTS] = results
        return data

    def fetch_coverage_etl_data(self, group_id, config):
        '''fetch median insert size and coverage QC metrics from QC-ETL'''
        self.etl_cache = QCETLCache(config[self.identifier]['qcetl_cache'])
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

    def fill_file_if_null(self, wrapper, ini_parameter_name, file_suffix):
        if wrapper.my_param_is_null(ini_parameter_name):
            path_info = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
            snv_count_path = path_info.get(file_suffix)
            if snv_count_path == None:
                msg = 'Cannot find {0} path'.format(ini_parameter_name)
                self.logger.error(msg)
                raise RuntimeError(msg)
            wrapper.set_my_param(ini_parameter_name,  snv_count_path)
        return(wrapper)
    
    def fill_qc_if_null(self, wrapper, config, parameter_name):
        if wrapper.my_param_is_null(parameter_name):
            work_dir = self.workspace.get_work_dir()
            if os.path.exists(os.path.join(work_dir,core_constants.DEFAULT_SAMPLE_INFO)):
                sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
                group_id = sample_info.get('tumour_id')
            else:
                msg = 'tumour_id not found for querying qc-etl, specify QC values in INI'
                self.logger.error(msg)
                raise RuntimeError(msg)
            qc_dict = self.fetch_coverage_etl_data(group_id, config)
            wrapper.set_my_param(parameter_name, int(qc_dict[parameter_name]))
        return(wrapper)
    
    def plot_insert_size(self, is_path, output_dir ):
        '''call R to plot insert size distribution'''
        args = [
            os.path.join(os.path.dirname(__file__),'insert_size_plot.R'),
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
    
    def preprocess_snv_count(self, snv_count_path ):
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
    
    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.SAMPLE_TEMPLATE_NAME, data)
    
    def specify_params(self):
        self.set_ini_default('qcetl_cache', self.QCETL_CACHE)
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