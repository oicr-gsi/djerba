"""
Run a diff between pairs of input and reference JSON reports
Generate an HTML summary
"""

import json
import logging
import os

import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.util.benchmark_tools import report_equivalence_tester
from djerba.util.date import get_timestamp
from djerba.util.render_mako import mako_renderer
from djerba.util.environment import directory_finder
from djerba.util.validator import path_validator

class main(plugin_base):

    PRIORITY = 10
    PLUGIN_VERSION = '0.0.1'
    TEMPLATE_NAME = 'benchmark_template.html'
    REPORT = 'report'
    REPORT_RESULTS = 'report_results'
    BODY = 'body'
    INPUT_FILE = 'input_file'
    REF_DIR = 'ref_dir'
    REF_FILE = 'ref_file'
    REF_FILE_NAME = 'bench_ref_paths.json'
    STATUS = 'status'
    STATUS_EMOJI = 'status_emoji'
    DIFF = 'diff'
    DIFF_NAME = 'diff_name'
    INPUT_NAME = 'input_name'
    RUN_TIME = 'run_time'
    NOT_FOUND = 'Not found'
    NOT_APPLICABLE = 'Not applicable'

    # __init__ is inherited from the parent class

    def compare_reports(self, input_paths, ref_paths, delta_path):
        input_set = set(input_paths.keys())
        ref_set = set(ref_paths.keys())
        report_results = []
        for report in sorted(list(input_set.union(ref_set))):
            # load the input and reference report JSON files
            # find status (and full-text diff, if any)
            # record for output JSON
            input_path = input_paths.get(report)
            ref_path = ref_paths.get(report)
            if input_path and ref_path:
                tester = report_equivalence_tester(
                    [input_path, ref_path], delta_path, self.log_level, self.log_path
                )
                status = tester.get_status()
                status_emoji = tester.get_status_emoji()
                diff = tester.get_diff_text()
            else:
                status = 'INCOMPLETE'
                status_emoji = '&#x2753;' # question mark
                diff = 'NA'
            input_file = input_paths.get(report, self.NOT_FOUND)
            ref_file = ref_paths.get(report, self.NOT_FOUND)
            if input_file == self.NOT_FOUND or ref_file == self.NOT_FOUND:
                diff_name = self.NOT_FOUND
            elif status == tester.IDENTICAL_STATUS:
                diff_name = self.NOT_APPLICABLE
            else:
                diff_name = report+"_diff.txt"
            result = {
                self.REPORT: report,
                self.STATUS: status,
                self.STATUS_EMOJI: status_emoji,
                self.DIFF: diff,
                self.DIFF_NAME: diff_name,
                self.INPUT_FILE: input_file,
                self.REF_FILE: ref_file
            }
            report_results.append(result)
        return report_results

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_param_if_null(self.INPUT_NAME, 'Unknown')
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        # validate the inputs
        attributes = wrapper.get_my_attributes()
        self.check_attributes_known(attributes)
        validator = path_validator(self.log_level, self.log_path)
        in_path = wrapper.get_my_string(self.INPUT_FILE)
        validator.validate_input_file(in_path)
        ref_dir = wrapper.get_my_string(self.REF_DIR)
        validator.validate_input_dir(ref_dir)
        # extract the data
        data = {
            'plugin_name': self.identifier+' plugin',
            'version': self.PLUGIN_VERSION,
            'priorities': wrapper.get_my_priorities(),
            'attributes': attributes,
            'merge_inputs': {}
        }
        with open(in_path) as in_file:
            input_paths = json.load(in_file)
        ref_paths = self.get_ref_paths(ref_dir, validator)
        delta_file = None # TODO make this configurable
        report_results = self.compare_reports(input_paths, ref_paths, delta_file)
        self.logger.debug('Found {0} report results'.format(len(report_results)))
        data['results'] = {
            self.INPUT_NAME: wrapper.get_my_string(self.INPUT_NAME),
            self.RUN_TIME: get_timestamp(),
            self.REPORT_RESULTS: report_results
        }
        return data

    def get_ref_paths(self, ref_dir, validator):
        # The ref_dir contains an index file, listing relative paths to Djerba JSON reports.
        # The index file contains a list of identifiers we expect to see.
        # Some identifiers from the index may be absent from the input data, eg. because of
        # workflow failures. This is shown in the HTML output.
        ref_index_path = os.path.join(ref_dir, self.REF_FILE_NAME)
        validator.validate_input_file(ref_index_path)
        with open(ref_index_path) as index_file:
            ref_index = json.loads(index_file.read())
        ref_index_full_paths = {}
        for key, val in ref_index.items():
            full_path = os.path.join(ref_dir, val)
            validator.validate_input_file(full_path)
            ref_index_full_paths[key] = full_path
        return ref_index_full_paths

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)

    def specify_params(self):
        self.set_ini_default(core_constants.ATTRIBUTES, 'research')
        self.set_priority_defaults(self.PRIORITY)
        self.add_ini_required(self.INPUT_FILE)
        self.add_ini_required(self.REF_DIR)
        self.add_ini_discovered(self.INPUT_NAME)
        #finder = directory_finder(self.log_level, self.log_path)
        #default_delta_path = 
