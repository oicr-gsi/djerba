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

class main(plugin_base):

    RESULTS_SUFFIX = '\.mrdetect\.txt$'
    VAF_SUFFIX = 'mrdetect.vaf.txt'
    HBC_SUFFIX = 'HBCs.csv'
    DEFAULT_CONFIG_PRIORITY = 200

    def __init__(self, workspace, identifier, log_level=logging.INFO, log_path=None):
        super().__init__(workspace, identifier, log_level, log_path)
        
        # Setting default parameters
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)

        # Setting required parameters
        self.add_ini_required('wgs_mutations')
        
        # Setting default parameters
        """Note: these are found and then populated in the fully specified ini."""
        self.set_ini_default('results_file', None)
        self.set_ini_default('vaf_file', None)
        self.set_ini_default('hbc_file', None)

    def configure(self, config):
        config = self.apply_defaults(config)
        config = self.set_all_priorities(config, self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        try:
            """this exception is only for testing purposes so I can specify the file in the .ini"""
            self.provenance = self.subset_provenance("mrdetect")
            config[self.identifier][constants.RESULTS_FILE] = self.parse_file_path(self.RESULTS_SUFFIX, self.provenance)
            config[self.identifier][constants.VAF_FILE] = self.parse_file_path(self.VAF_SUFFIX, self.provenance)
            config[self.identifier][constants.HBC_FILE] = self.parse_file_path(self.HBC_SUFFIX, self.provenance)
            self.logger.info("PWGS ANALYSIS: Files pulled from Provenance")
        except OSError:
            self.logger.info("PWGS ANALYSIS: Files pulled from ini")

        hbc_results = self.preprocess_hbc(config[self.identifier][constants.HBC_FILE])
        reads_detected = self.preprocess_vaf(config[self.identifier][constants.VAF_FILE])
        mrdetect_results = self.preprocess_results(config[self.identifier][constants.RESULTS_FILE])
        pwgs_base64 = self.write_pwgs_plot(config[self.identifier][constants.HBC_FILE], 
                                           config[self.identifier][constants.VAF_FILE],
                                           output_dir = self.workspace.print_location())
        self.logger.info("PWGS ANALYSIS: Finished preprocessing files")       
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': self.get_my_priorities(config),
            'attributes': self.get_my_attributes(config),
            'merge_inputs': {
            },
            'results': {
                'outcome': mrdetect_results['outcome'],
                'significance_text': mrdetect_results['significance_text'],
                'TFZ': mrdetect_results['TF'],
                'TFR': float('%.1E' % Decimal( reads_detected / hbc_results['reads_checked'] ))*100 ,
                'sites_checked': hbc_results['sites_checked'],
                'reads_checked': hbc_results['reads_checked'],
                'sites_detected': hbc_results['sites_detected'],
                'reads_detected': reads_detected,
                'p-value': mrdetect_results['pvalue'],
                'hbc_n': hbc_results['hbc_n'],
                'pwgs_base64': pwgs_base64
            }
        }
        self.join_WGS_data(wgs_file = config[self.identifier][constants.WGS_MUTATIONS], 
                           vaf_file = config[self.identifier][constants.VAF_FILE], 
                           groupid = config['core'][constants.GROUP_ID],
                           output_dir = self.workspace.print_location())
        self.workspace.write_json('hbc_results.json', hbc_results)
        self.workspace.write_json('mrdetect_results.json', mrdetect_results)
        return data

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
        hbc_dict = {'sites_checked': int(sites_checked[0]),
                    'reads_checked': int(reads_checked[0]),
                    'sites_detected': int(sites_detected[0]),
                    'hbc_n': hbc_n}
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
    
    def preprocess_results(self, results_path):
        """
        pull data from results file
        """
        results_dict = {}
        with open(results_path, 'r') as hbc_file:
            reader_file = csv.reader(hbc_file, delimiter="\t")
            next(reader_file, None)
            for row in reader_file:
                try:
                    results_dict = {
                                    'TF': float('%.1E' % Decimal(row[7]))*100,
                                    'pvalue':  float('%.3E' % Decimal(row[10]))
                                    }
                except IndexError as err:
                    msg = "Incorrect number of columns in vaf row: '{0}' ".format(row)+\
                          "read from '{0}'".format(results_path)
                    raise RuntimeError(msg) from err
        if results_dict['pvalue'] > float(constants.DETECTION_ALPHA) :
            significance_text = "not significantly larger"
            results_dict['outcome'] = "NEGATIVE"
            results_dict['TF'] = 0
        elif results_dict['pvalue'] <= float(constants.DETECTION_ALPHA):
            significance_text = "significantly larger"
            results_dict['outcome'] = "POSITIVE"
        else:
            msg = "results pvalue {0} incompatible with detection alpha {1}".format(results_dict['pvalue'], constants.DETECTION_ALPHA)
            self.logger.error(msg)
            raise RuntimeError
        results_dict['significance_text'] = significance_text
        return results_dict
    
    def write_pwgs_plot(self, hbc_path, vaf_file, output_dir ):
        args = [
            os.path.join(constants.RSCRIPTS_LOCATION,'detection.plot.R'),
            '--hbc_results', hbc_path,
            '--vaf_results', vaf_file,
            '--output_directory', output_dir 
        ]
        pwgs_results = subprocess_runner().run(args)
        return(pwgs_results.stdout.split('"')[1])
    
    def join_WGS_data(self, wgs_file, vaf_file, groupid, output_dir ):
        args = [
            os.path.join(constants.RSCRIPTS_LOCATION,'WGS.join.R'),
            '--wgs_input', wgs_file,
            '--vaf_results', vaf_file,
            '--groupid', groupid,
            '--output_directory', output_dir 
        ]
        subprocess_runner().run(args)
    
    def _get_most_recent_row(self, rows):
        # if input is empty, raise an error
        # otherwise, return the row with the most recent date field (last in lexical sort order)
        # rows may be an iterator; if so, convert to a list
        rows = list(rows)
        if len(rows)==0:
            msg = "Empty input to find most recent row; no rows meet filter criteria?"
            self.logger.debug(msg)
            raise MissingProvenanceError(msg)
        else:
            return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]
        
    def parse_file_path(self, file_pattern, provenance):
        # get most recent file of given workflow, metatype, file path pattern, and sample name
        # self._filter_* functions return an iterator
        iterrows = self._filter_file_path(file_pattern, rows=provenance)
        try:
            row = self._get_most_recent_row(iterrows)
            path = row[index.FILE_PATH]
        except MissingProvenanceError as err:
            msg = "No provenance records meet filter criteria: path-regex = {0}.".format(file_pattern)
            self.logger.debug(msg)
            path = None
        return path
    
    def _filter_file_path(self, pattern, rows):
        return filter(lambda x: re.search(pattern, x[index.FILE_PATH]), rows)
    
    def subset_provenance(self, workflow):
        provenance = []
        with self.workspace.open_gzip_file(constants.PROVENANCE_OUTPUT) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            for row in reader:
                if row[index.WORKFLOW_NAME] == workflow:
                    provenance.append(row)
        return(provenance)

    
class MissingProvenanceError(Exception):
    pass
