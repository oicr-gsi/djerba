"""Main class for mini-Djerba"""

import json
import logging
import os
import djerba.core.constants as cc
import djerba.util.mini.constants as constants
from configparser import ConfigParser
from time import strftime
from djerba.core.main import main_base
from djerba.plugins.patient_info.plugin import main as patient_info_plugin
from djerba.plugins.summary.plugin import main as summary_plugin
from djerba.plugins.supplement.body.plugin import main as supplement_plugin
from djerba.util.args import arg_processor_base
from djerba.util.logger import logger
from djerba.util.mini.mdc import mdc
from djerba.util.validator import path_validator
from djerba.version import get_djerba_version

class main(main_base):

    PATIENT_INFO = 'patient_info'
    SUPPLEMENT = 'supplement.body'
    SUMMARY = 'summary'
    SUMMARY_FILENAME = 'summary.txt'

    def get_supplement_params(self, mdc_supplement, data):
        # want to configure the supplement.body plugin with new keys from MDC:
        # - report_signoff_date (defaults to current date)
        # - clinical_geneticist_name
        # - clinical_geneticist_licence
        #
        # other config params (eg. date of CGI draft) retain original values from JSON
        supplement = data[cc.CONFIG][self.SUPPLEMENT]
        for key in mdc_supplement.keys():
            supplement[key] = mdc_supplement.get(key)
        return supplement

    def render(self, json_path, out_dir, pdf):
        """
        Simple rendering to HTML/PDF for an existing JSON file
        """
        with open(json_path) as in_file:
            data = json.loads(in_file.read())
        self.base_render(data, out_dir, pdf)

    def run(self, args):
        """
        Process command-line args and run 'setup', 'render' or 'update'
        """
        ap = arg_processor(args, self.logger, validate=False)
        mode = ap.get_mode()
        if mode == constants.SETUP:
            self.setup(
                ap.get_out_file(),
                ap.get_json()
            )
        elif mode == constants.RENDER:
            self.render(
                ap.get_json(),
                ap.get_out_dir(),
                ap.is_pdf_enabled()
            )
        elif mode == constants.UPDATE:
            self.update(
                ap.get_config_path(),
                ap.get_json(),
                ap.get_out_dir(),
                ap.is_pdf_enabled(),
                ap.is_write_json_enabled(),
                ap.is_forced()
            )
        else:
            msg = "Mode '{0}' is not defined in Djerba mini.main!".format(mode)
            self.logger.error(msg)
            raise RuntimeError(msg)

    def setup(self, out_path, json_path):
        """
        Read an existing JSON file (if any), write an MDC file ready for editing
        MDC contains placeholder values for PHI, and summary text from the JSON
        """
        if json_path == None:
            patient_info = patient_info_plugin.PATIENT_DEFAULTS
            text = 'Patient summary text goes here'
            supplement = {
                supplement_plugin.REPORT_SIGNOFF_DATE: strftime('%Y/%m/%d'),
                supplement_plugin.GENETICIST: supplement_plugin.GENETICIST_DEFAULT,
                supplement_plugin.GENETICIST_ID: supplement_plugin.GENETICIST_ID_DEFAULT
            }
        else:
            with open(json_path, encoding=cc.TEXT_ENCODING) as in_file:
                data = json.loads(in_file.read())
            patient_info = data[cc.PLUGINS][self.PATIENT_INFO][cc.RESULTS]
            supplement = data[cc.PLUGINS][self.PATIENT_INFO][cc.RESULTS]
            text = data[cc.PLUGINS][self.SUMMARY][cc.RESULTS][summary_plugin.SUMMARY_TEXT]
        mdc(self.log_level, self.log_path).write(out_path, patient_info, supplement, text)

    def update(self, config_path, json_path, out_dir, pdf, write_json, force):
        """
        Differs from update method in core:
        - MDC instead of INI/TXT as config
        - No archive capability
        - Always write (at least) HTML output
        """
        # read the config file and generate a ConfigParser on-the-fly
        # write summary text to the workspace
        # run configure step to populate default values
        # then run extraction to get the data structure for update
        mdc_handler = mdc(self.log_level, self.log_path)
        [patient_info, supplement_mdc, summary_text] = mdc_handler.read(config_path)
        with open(json_path) as json_file:
            old_json = json.loads(json_file.read())
        config = ConfigParser()
        # core params (eg. the CGI author name) are unchanged from the input JSON
        config.add_section(cc.CORE)
        core_params = old_json[cc.CONFIG][cc.CORE]
        for k in core_params.keys():
            config.set(cc.CORE, k, core_params[k])
        # patient info params are all taken from the MDC file
        config.add_section(self.PATIENT_INFO)
        for k in patient_info.keys():
            config.set(self.PATIENT_INFO, k, patient_info[k])
        config.add_section(self.SUPPLEMENT)
        # supplementary params are a mix of MDC params and existing JSON defaults
        supplement_params = self.get_supplement_params(supplement_mdc, old_json)
        for k in supplement_params.keys():
            config.set(self.SUPPLEMENT, k, str(supplement_params[k]))
        config.add_section(self.SUMMARY)
        summary_path = os.path.join(self.work_dir, self.SUMMARY_FILENAME)
        with open(summary_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
            print(summary_text, file=out_file)
        config.set('summary', summary_plugin.SUMMARY_FILE, summary_path)
        config = self.configure_from_parser(config)
        data_new = self.base_extract(config)
        data = self.update_data_from_file(data_new, json_path, force)
        self.base_render(data, out_dir, pdf)
        if write_json:
            json_path = os.path.join(out_dir, 'updated_report.json')
            with open(json_path, 'w') as out_file:
                print(json.dumps(data), file=out_file)

class arg_processor(arg_processor_base):

    def validate_args(self, args):
        """
        Check we can read/write paths in command-line arguments
        Assume logging has been initialized and log path (if any) is valid
        """
        self.logger.info("Validating paths in command-line arguments")
        v = path_validator(self.log_level, self.log_path)
        if args.subparser_name == constants.SETUP:
            if args.json != None:
                v.validate_input_file(args.json)
            v.validate_output_file(args.out)
        elif args.subparser_name == constants.RENDER:
            v.validate_input_file(args.json)
            v.validate_output_dir(args.out_dir)
            if args.work_dir != None: # work_dir is optional
                v.validate_output_dir(args.work_dir)
        elif args.subparser_name == constants.UPDATE:
            v.validate_input_file(args.config)
            v.validate_input_file(args.json)
            v.validate_output_dir(args.out_dir)
            if args.work_dir != None: # work_dir is optional
                v.validate_output_dir(args.work_dir)
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: " + args.subparser_name)
        self.logger.info("Command-line path validation finished.")

    def get_config_path(self):
        return self._get_arg('config')

    def get_json_path(self):
        return self._get_arg('json')

    def get_out_file(self):
        return self._get_arg('out')

class MiniDjerbaScriptError(Exception):
    pass

