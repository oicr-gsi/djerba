"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import re
import logging

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools

class main(plugin_base):

    RESULTS_SUFFIX = '\.mrdetect\.txt$'
    VAF_SUFFIX = 'mrdetect.vaf.txt'
    HBC_SUFFIX = 'HBCs.csv'
    DEFAULT_CONFIG_PRIORITY = 200

    # TO DO, REMOVE
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def specify_params(self):
        # Setting default parameters
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)

        # Setting default parameters
        """Note:in the fully specified ini, these are found and populated """
        self.set_ini_default('results_file', None)
        self.set_ini_default('vaf_file', None)
        self.set_ini_default('hbc_file', None)

        # Setting required parameters
        self.add_ini_required('wgs_mutations')
        self.add_ini_required('group_id')

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_priorities(self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        groupid = config[self.identifier][constants.GROUP_ID]
        mrdetect_results = pwgs_tools.preprocess_results(self, config[self.identifier][constants.RESULTS_FILE], groupid)
        # TO DO, MOVE TO CONFIGURE
        hbc_results = self.preprocess_hbc(config[self.identifier][constants.HBC_FILE], groupid)
        vaf_results = self.preprocess_vaf(config[self.identifier][constants.VAF_FILE], groupid)
        pwgs_base64 = self.write_pwgs_plot(hbc_results['hbc_file'], 
                                           vaf_results['vaf_path'],
                                           output_dir = self.workspace.print_location())
        self.logger.info("PWGS ANALYSIS: Finished preprocessing files")       
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {
            },
            'results': {
                'outcome': mrdetect_results['outcome'],
                'significance_text': mrdetect_results['significance_text'],
                'TFR': float('%.1E' % Decimal( vaf_results['reads_detected']*100 / hbc_results['reads_checked'] )),
                'sites_checked': hbc_results['sites_checked'],
                'reads_checked': hbc_results['reads_checked'],
                'sites_detected': hbc_results['sites_detected'],
                'reads_detected': vaf_results['reads_detected'],
                'p-value': mrdetect_results['pvalue'],
                'hbc_n': hbc_results['hbc_n'],
                'pwgs_base64': pwgs_base64,
                'files': {
                    'results_file': mrdetect_results['results_path'],
                    'hbc_results': hbc_results["hbc_file"],
                    'vaf_results': vaf_results["vaf_path"]
                }
            },
            'version': str(constants.PWGS_DJERBA_VERSION)
        }
        self.join_WGS_data(wgs_file = config[self.identifier][constants.WGS_MUTATIONS], 
                           vaf_file = vaf_results['vaf_path'], 
                           groupid = groupid,
                           output_dir = self.workspace.print_location())
        self.workspace.write_json('hbc_results.json', hbc_results)
        self.workspace.write_json('mrdetect_results.json', mrdetect_results)
        return data

    def join_WGS_data(self, wgs_file, vaf_file, groupid, output_dir ):
        args = [
            os.path.join(constants.RSCRIPTS_LOCATION,'WGS.join.R'),
            '--wgs_input', wgs_file,
            '--vaf_results', vaf_file,
            '--groupid', groupid,
            '--output_directory', output_dir 
        ]
        subprocess_runner().run(args)
        
    def preprocess_hbc(self, hbc_path, group_id = 'None'):
        """
        summarize healthy blood controls (HBC) file
        """
        if hbc_path == 'None':
            provenance = pwgs_tools.subset_provenance(self, "mrdetect", group_id)
            try:
                hbc_path = pwgs_tools.parse_file_path(self, self.HBC_SUFFIX, provenance)
            except OSError as err:
                msg = "File from workflow {0} with extension {1} was not found in Provenance subset file '{2}' not found".format("mrdetect", self.HBC_SUFFIX, constants.PROVENANCE_OUTPUT)
                raise RuntimeError(msg) from err
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
        hbc_dict = {'sites_checked': int(sites_checked[0]),
                    'reads_checked': int(reads_checked[0]),
                    'sites_detected': int(sites_detected[0]),
                    'hbc_n': hbc_n,
                    'hbc_file': hbc_path}
        return hbc_dict
    
    def preprocess_vaf(self, vaf_path, group_id = 'None'):
        """
        summarize Variant Allele Frequency (VAF) file
        """
        if vaf_path == 'None':
            provenance = pwgs_tools.subset_provenance(self, "mrdetect", group_id)
            try:
                vaf_path = pwgs_tools.parse_file_path(self, self.VAF_SUFFIX, provenance)
            except OSError as err:
                msg = "File from workflow {0} with extension {1} was not found in Provenance subset file '{2}' not found".format("mrdetect", self.VAF_SUFFIX, constants.PROVENANCE_OUTPUT)
                raise RuntimeError(msg) from err
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
        vaf_dict = {'vaf_path': vaf_path,
                    'reads_detected': reads_detected
                    }        
        return vaf_dict
    
    def render(self, data):
        args = data
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'html'
        ))
        report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
        mako_template = report_lookup.get_template(constants.ANALYSIS_TEMPLATE_NAME)
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            raise
        return html    
    
    def write_pwgs_plot(self, hbc_path, vaf_file, output_dir ):
        args = [
            os.path.join(constants.RSCRIPTS_LOCATION,'detection.plot.R'),
            '--hbc_results', hbc_path,
            '--vaf_results', vaf_file,
            '--output_directory', output_dir,
            '--pval', str(constants.DETECTION_ALPHA)
        ]
        pwgs_results = subprocess_runner().run(args)
        return(pwgs_results.stdout.split('"')[1])
    
