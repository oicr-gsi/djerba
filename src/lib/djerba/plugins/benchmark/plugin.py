"""
Run a diff between pairs of input and reference JSON reports
Generate an HTML summary
"""

import json
import logging

import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.util.benchmark import report_equivalence_tester
from djerba.util.render_mako import mako_renderer
from djerba.util.environment import directory_finder
from djerba.util.validator import path_validator

class main(plugin_base):

    PRIORITY = 10
    PLUGIN_VERSION = '0.0.1'
    TEMPLATE_NAME = 'benchmark_template.html'
    INPUT_FILE = 'input_file'
    REF_FILE = 'ref_file'
    STATUS = 'status'
    DIFF = 'diff'

    # __init__ is inherited from the parent class

    def compare_reports(self, input_path, ref_path, delta_path):
        with open(input_path) as in_file:
            input_paths = json.load(in_file)
        with open(ref_path) as in_file:
            ref_paths = json.load(in_file)
        input_set = set(input_paths.keys())
        ref_set = set(ref_paths.keys())
        donors = []
        for donor in sorted(list(input_set.union(ref_set))):
            if donor in input_set:
                if donor in ref_set:
                    donors.append(donor)
                    self.logger.debug("Found inputs and reference for donor "+donor)
                else:
                    self.logger.warning("Input but no reference for donor "+donor)
            else:
                self.logger.warning("Reference but no input for donor "+donor)
        results = {}
        for donor in donors:
            # load the input and reference report JSON files
            # find status (and full-text diff, if any)
            # record for output JSON
            reports = [input_paths[donor], ref_paths[donor]]
            tester = report_equivalence_tester(
                reports, delta_path, self.log_level, self.log_path
            )
            status = tester.get_status()
            diff = tester.get_diff_text()
            results[donor] = {
                self.STATUS: status,
                self.DIFF: diff,
                self.INPUT_FILE: input_paths[donor],
                self.REF_FILE: ref_paths[donor]
            }
        return results

    def configure(self, config):
        config = self.apply_defaults(config)
        return config

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
        results = self.compare_reports(input_file, ref_file, delta_file)
        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)

    def specify_params(self):
        self.set_ini_default(core_constants.ATTRIBUTES, 'research')
        self.set_priority_defaults(self.PRIORITY)
        self.add_ini_required(self.INPUT_FILE)
        self.add_ini_required(self.REF_FILE)
        #finder = directory_finder(self.log_level, self.log_path)
        #default_delta_path = 
