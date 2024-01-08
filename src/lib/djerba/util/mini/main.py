"""Main class for mini-Djerba"""

import json
import logging
import os
import djerba.core.constants as cc
import djerba.util.mini.constants as constants
from tempfile import TemporaryDirectory
from djerba.core.main import main_base
from djerba.plugins.summary.plugin import main as summary_plugin
from djerba.util.args import arg_processor_base
from djerba.util.logger import logger
from djerba.util.mini.mdc import mdc
from djerba.util.validator import path_validator
from djerba.version import get_djerba_version

class main(main_base):

    SUMMARY_NAME = 'summary.txt'

    def ready(self, out_path, json_path):
        """
        Read an existing JSON file, write an MDC file ready for editing
        MDC contains placeholder values for PHI, and summary text from the JSON
        """
        with open(json_path, encoding=cc.TEXT_ENCODING) as in_file:
            data = json.loads(in_file.read())
        patient_info = data[cc.PLUGINS]['patient_info'][cc.RESULTS]
        text = data[cc.PLUGINS]['summary'][cc.RESULTS][summary_plugin.SUMMARY_TEXT]
        mdc(self.log_level, self.log_path).write(out_path, patient_info, text)

    def run(self, args):
        """
        Process command-line args and run either 'ready' or 'update'
        """
        ap = arg_processor(args, self.logger, validate=False)
        mode = ap.get_mode()
        if mode == constants.READY:
            self.ready(
                ap.get_out_file(),
                ap.get_json_path()
            )
        elif mode == constants.UPDATE:
            self.update(
                ap.get_config_path(),
                ap.get_json_path(),
                ap.get_out_dir(),
                ap.is_pdf_enabled(),
                ap.is_write_json_enabled()
            )
        else:
            msg = "Mode '{0}' is not defined in Djerba mini.main!".format(mode)
            self.logger.error(msg)
            raise RuntimeError(msg)

    def update(self, config_path, json_path, out_dir, pdf, write_json):
        """
        Differs from update method in core:
        - MDC instead of INI/TXT as config
        - No archive capability
        - Always write (at least) HTML output
        """
        # read the config file and generate a ConfigParser
        # write summary text to a temporary file
        # then run extraction to get the data structure for update
        [update_config, update_text] = mdc(self.log_level, self.log_path).read(config_path)
        update_config = self.configure_from_parser(update_config)
        summary_path = os.path.join(self.work_dir, self.SUMMARY_NAME)
        with open(summary_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
            print(update_text, file=out_file)
        update_config.set('summary', summary_plugin.SUMMARY_FILE, summary_path)
        data_new = self.base_extract(update_config)
        data = self.update_data_from_file(data_new, json_path)
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
        if args.subparser_name == constants.READY:
            v.validate_input_file(args.json)
            v.validate_output_file(args.out)
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

    def is_write_json_enabled(self):
        return self._get_arg('write_json')

