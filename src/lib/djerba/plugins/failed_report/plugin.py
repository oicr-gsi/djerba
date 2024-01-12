"""
Plugin to generate the failed report results summary report section

"""

import logging
from time import strftime
import csv
import os
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
from djerba.core.workspace import workspace

class main(plugin_base):

    PRIORITY = 600
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'failed_report_template.html'
    FAILED_TEMPLATE_FILE = 'failed_template.txt'
    FAILED_FILE = 'failed_file'
    FAILED_TEXT = 'failed_text'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()

        # Parameters for the sentence.
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            input_params_helper.PRIMARY_CANCER,
            input_params_helper.PRIMARY_CANCER
        )        
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            input_params_helper.ASSAY,
            input_params_helper.ASSAY
        )        
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            input_params_helper.STUDY,
            input_params_helper.STUDY
        )        
          
        # Get the parameters from the config
        primary_cancer = config[self.identifier][input_params_helper.PRIMARY_CANCER]
        assay = config[self.identifier][input_params_helper.ASSAY]
        study = config[self.identifier][input_params_helper.STUDY]

        # Write the failed text if there isn't one already specified.
        if wrapper.my_param_is_null(self.FAILED_FILE):
            failed_template_path = os.path.join(work_dir, self.FAILED_TEMPLATE_FILE)
            self.write_failed_text(failed_template_path, primary_cancer, assay, study)
            wrapper.set_my_param(self.FAILED_FILE, failed_template_path)

        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        failed_text = self.read_failed_text(config[self.identifier][self.FAILED_FILE])
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

        # Construct failed text with parameters.

        data[core_constants.RESULTS][self.FAILED_TEXT] = failed_text
        self.workspace.write_string('results_summary.txt', failed_text)
        return data

    def specify_params(self):
        discovered = [
            self.FAILED_FILE,
            input_params_helper.PRIMARY_CANCER,
            input_params_helper.ASSAY,
            input_params_helper.STUDY
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'failed')
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

    def write_failed_text(self, failed_template_path, primary_cancer, assay, study):
        
        failed_text = "The patient has been diagnosed with " + primary_cancer +  \
                       " and has been referred for the OICR Genomics " + assay + \
                       " assay through the " + study + " study." + \
                       " A quality failure report for this sample / is being issued due to the informatically inferred tumour purity of ...% which is below the reportable threshold of 30% for the assay / is being issued due to failed extraction / is being issued as the quantity of extracted DNA/RNA from tissue material was below the lower quantifiable range and therefore below the minimum input amount for this assay (minimums of 25ng for DNA and 50ng for RNA)..."
        
        with open(failed_template_path, "w") as failed_file:
            failed_file.write(failed_text)
  

    def read_failed_text(self, results_failed_path):
        """
        read results summary from file
        """
        with open(results_failed_path, 'r') as failed_file:
            failed_text = csv.reader(failed_file, delimiter="\t")
            text = ''
            for row in failed_text:
                text = text.join(row)
        return text
