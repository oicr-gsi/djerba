"""Main class for mini-Djerba"""

import json
import logging
import os
import djerba.core.constants as cc
import djerba.util.mini.constants as constants
from configparser import ConfigParser
from djerba.core.main import main_base
from djerba.plugins.patient_info.plugin import main as patient_info_plugin
from djerba.plugins.summary.plugin import main as summary_plugin
from djerba.util.args import arg_processor_base
from djerba.util.logger import logger
from djerba.util.mini.mdc import mdc
from djerba.util.validator import path_validator
from djerba.version import get_djerba_version

class main(main_base):

    PATIENT_INFO = 'patient_info'
    SUMMARY = 'summary'
    SUMMARY_FILENAME = 'summary.txt'

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
        else:
            with open(json_path, encoding=cc.TEXT_ENCODING) as in_file:
                data = json.loads(in_file.read())
            patient_info = data[cc.PLUGINS][self.PATIENT_INFO][cc.RESULTS]
            text = data[cc.PLUGINS][self.SUMMARY][cc.RESULTS][summary_plugin.SUMMARY_TEXT]
        mdc(self.log_level, self.log_path).write(out_path, patient_info, text)

    def update(self, config_path, json_path, out_dir, pdf, write_json, force):
        """
        Differs from update method in core:
        - MDC instead of INI/TXT as config
        - No archive capability
        - Always write (at least) HTML output
        """
        # read the config file and generate a ConfigParser
        # write summary text to the workspace
        # run configure step to populate default values
        # then run extraction to get the data structure for update
        [patient_info, summary_text] = mdc(self.log_level, self.log_path).read(config_path)
        config = ConfigParser()
        config.add_section(cc.CORE)
        config.add_section(self.PATIENT_INFO)
        for k in patient_info.keys():
            config.set(self.PATIENT_INFO, k, patient_info[k])
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

