"""
Run a diff between pairs of input and reference JSON reports
Generate an HTML summary
"""

import json
import logging

import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.util.benchmark import report_equivalence_tester
from djerba.util.date import get_timestamp
from djerba.util.render_mako import mako_renderer
from djerba.util.environment import directory_finder
from djerba.util.validator import path_validator

class main(plugin_base):

    PRIORITY = 10
    PLUGIN_VERSION = '0.0.1'
    TEMPLATE_NAME = 'benchmark_template.html'
    DONOR = 'donor'
    DONOR_RESULTS = 'donor_results'
    BODY = 'body'
    INPUT_FILE = 'input_file'
    REF_FILE = 'ref_file'
    STATUS = 'status'
    STATUS_EMOJI = 'status_emoji'
    DIFF = 'diff'
    DIFF_NAME = 'diff_name'
    INPUT_NAME = 'input_name'
    RUN_TIME = 'run_time'
    NOT_FOUND = 'Not found'
    NOT_APPLICABLE = 'Not applicable'

    # __init__ is inherited from the parent class

    def compare_reports(self, inputs_path, refs_path, delta_path):
        with open(inputs_path) as in_file:
            input_paths = json.load(in_file)
        with open(refs_path) as in_file:
            ref_paths = json.load(in_file)
        input_set = set(input_paths.keys())
        ref_set = set(ref_paths.keys())
        donor_results = []
        for donor in sorted(list(input_set.union(ref_set))):
            # load the input and reference report JSON files
            # find status (and full-text diff, if any)
            # record for output JSON
            input_path = input_paths.get(donor)
            ref_path = ref_paths.get(donor)
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
            input_file = input_paths.get(donor, self.NOT_FOUND)
            ref_file = ref_paths.get(donor, self.NOT_FOUND)
            if input_file == self.NOT_FOUND or ref_file == self.NOT_FOUND:
                diff_name = self.NOT_FOUND
            elif status == tester.IDENTICAL_STATUS:
                diff_name = self.NOT_APPLICABLE
            else:
                diff_name = donor+"_diff.txt"
            result = {
                self.DONOR: donor,
                self.STATUS: status,
                self.STATUS_EMOJI: status_emoji,
                self.DIFF: diff,
                self.DIFF_NAME: diff_name,
                self.INPUT_FILE: input_file,
                self.REF_FILE: ref_file
            }
            donor_results.append(result)
        return donor_results

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_param_if_null(self.INPUT_NAME, 'Unknown')
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        attributes = wrapper.get_my_attributes()
        self.check_attributes_known(attributes)
        data = {
            'plugin_name': self.identifier+' plugin',
            'version': self.PLUGIN_VERSION,
            'priorities': wrapper.get_my_priorities(),
            'attributes': attributes,
            'merge_inputs': {}
        }
        input_file = wrapper.get_my_string(self.INPUT_FILE)
        ref_file = wrapper.get_my_string(self.REF_FILE)
        validator = path_validator(self.log_level, self.log_path)
        validator.validate_input_file(input_file)
        validator.validate_input_file(ref_file)
        delta_file = None # TODO make this configurable
        donor_results = self.compare_reports(input_file, ref_file, delta_file)
        self.logger.debug('Found {0} donor results'.format(len(donor_results)))
        data['results'] = {
            self.INPUT_NAME: wrapper.get_my_string(self.INPUT_NAME),
            self.RUN_TIME: get_timestamp(),
            self.DONOR_RESULTS: donor_results
        }
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)

    def specify_params(self):
        self.set_ini_default(core_constants.ATTRIBUTES, 'research')
        self.set_priority_defaults(self.PRIORITY)
        self.add_ini_required(self.INPUT_FILE)
        self.add_ini_required(self.REF_FILE)
        self.add_ini_discovered(self.INPUT_NAME)
        #finder = directory_finder(self.log_level, self.log_path)
        #default_delta_path = 
