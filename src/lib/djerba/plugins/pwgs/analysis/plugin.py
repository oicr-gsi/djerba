"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import re
import logging

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as pc
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '1.1'
    
    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        group_id = config[self.identifier][pc.GROUP_ID]
        if wrapper.my_param_is_null(pc.RESULTS_FILE):
            wrapper.set_my_param(pc.RESULTS_FILE, pwgs_tools.subset_provenance(self, "mrdetect", group_id, pc.RESULTS_SUFFIX))
        if wrapper.my_param_is_null(pc.VAF_FILE):
            wrapper.set_my_param(pc.VAF_FILE, pwgs_tools.subset_provenance(self, "mrdetect", group_id, pc.VAF_SUFFIX))
        if wrapper.my_param_is_null(pc.HBC_FILE):
            wrapper.set_my_param(pc.HBC_FILE, pwgs_tools.subset_provenance(self, "mrdetect", group_id, pc.HBC_SUFFIX))
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        mrdetect_results = pwgs_tools.preprocess_results(self, config[self.identifier][pc.RESULTS_FILE])
        hbc_results = self.preprocess_hbc(config[self.identifier][pc.HBC_FILE])
        reads_detected = self.preprocess_vaf(config[self.identifier][pc.VAF_FILE])
        pwgs_base64 = self.write_pwgs_plot(config[self.identifier][pc.HBC_FILE], 
                                           config[self.identifier][pc.VAF_FILE],
                                           output_dir = self.workspace.print_location())
        self.logger.info("PWGS ANALYSIS: Finished preprocessing files")
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)       
        results =  {
                pc.CTDNA_OUTCOME: mrdetect_results[pc.CTDNA_OUTCOME],
                pc.SIGNIFICANCE: mrdetect_results[pc.SIGNIFICANCE],
                pc.TUMOUR_FRACTION_READS: float('%.1E' % Decimal( reads_detected*100 / hbc_results[pc.READS_CHECKED] )),
                pc.SITES_CHECKED: hbc_results[pc.SITES_CHECKED],
                pc.READS_CHECKED: hbc_results[pc.READS_CHECKED],
                pc.SITES_DETECTED: hbc_results[pc.SITES_DETECTED],
                pc.READS_DETECTED: reads_detected,
                pc.PVALUE: mrdetect_results[pc.PVALUE],
                pc.COHORT_N: hbc_results[pc.COHORT_N],
                'pwgs_base64': pwgs_base64,
                'files': {
                    'results_file': config[self.identifier][pc.RESULTS_FILE],
                    'hbc_results': config[self.identifier][pc.HBC_FILE],
                    'vaf_results': config[self.identifier][pc.VAF_FILE]
                }
            }
        data[pc.RESULTS] = results
        self.workspace.write_json('hbc_results.json', hbc_results)
        self.workspace.write_json('mrdetect_results.json', mrdetect_results)
        return data

    def preprocess_hbc(self, hbc_path):
        """
        summarize healthy blood controls (HBC) file
        """
        sites_checked = []
        reads_checked = []
        sites_detected = []
        with open(hbc_path, 'r') as hbc_file:
            reader_file = csv.reader(hbc_file, delimiter=",")
            next(reader_file, None)
            for row in reader_file:
                try:
                    sites_checked.append(row[2])
                    reads_checked.append(row[3])
                    sites_detected.append(row[4])
                except IndexError as err:
                    msg = "Incorrect number of columns in HBC row: '{0}'".format(row)+\
                        "read from '{0}'".format(hbc_path)
                    raise RuntimeError(msg) from err
        hbc_n = len(sites_detected) - 1
        hbc_dict = {pc.SITES_CHECKED: int(sites_checked[0]),
                    pc.READS_CHECKED: int(reads_checked[0]),
                    pc.SITES_DETECTED: int(sites_detected[0]),
                    pc.COHORT_N: hbc_n}
        return hbc_dict
    
    def preprocess_vaf(self, vaf_path):
        """
        summarize Variant Allele Frequency (VAF) file
        """
        reads_detected = 0
        with open(vaf_path, 'r') as hbc_file:
            reader_file = csv.reader(hbc_file, delimiter="\t")
            next(reader_file, None)
            for row in reader_file:
                try: 
                    reads_tmp = row[1]
                    reads_detected = reads_detected + int(reads_tmp)
                except IndexError as err:
                    msg = "Incorrect number of columns in vaf row: '{0}' ".format(row)+\
                          "read from '{0}'".format(vaf_path)
                    raise RuntimeError(msg) from err      
        return reads_detected
    
    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.ANALYSIS_TEMPLATE_NAME, data)
    
    def specify_params(self):
        discovered = [
            pc.RESULTS_FILE,
            pc.VAF_FILE,
            pc.HBC_FILE
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.add_ini_required(pc.GROUP_ID)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def write_pwgs_plot(self, hbc_path, vaf_file, output_dir ):
        '''
        use R to plot the detection rate 
        compared to healthy blood control, 
        return in base64
        '''
        args = [
            os.path.join(os.path.dirname(__file__),'detection.plot.R'),
            '--hbc_results', hbc_path,
            '--vaf_results', vaf_file,
            '--output_directory', output_dir,
            '--pval', str(pc.DETECTION_ALPHA)
        ]
        pwgs_results = subprocess_runner().run(args)
        return(pwgs_results.stdout.split('"')[1])
    
