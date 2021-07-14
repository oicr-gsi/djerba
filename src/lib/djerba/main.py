"""Main class to run Djerba"""

import configparser
import logging
import os
import tempfile

import djerba.util.constants as constants
from djerba.configure import configurer
from djerba.extract.extractor import extractor
from djerba.render import html_renderer
from djerba.render import pdf_renderer
from djerba.util.logger import logger
from djerba.util.validator import config_validator, path_validator

class main(logger):

    """Main class to run Djerba"""
    
    INI_DEFAULT_NAME = 'defaults.ini'
    
    def __init__(self):
        source_dir = os.path.dirname(os.path.realpath(__file__))
        self.ini_defaults = os.path.join(source_dir, constants.DATA_DIR_NAME, self.INI_DEFAULT_NAME)

    def read_config(self, ini_path):
        """Read INI config from the given path"""
        ini_config = configparser.ConfigParser()
        ini_config.read(self.ini_defaults)
        ini_config.read(ini_path) # overwrites the defaults
        return ini_config

    def run(self, args):
        """Main method to run Djerba"""
        self.validate_args(args)
        lv = self.get_log_level(args.debug, args.verbose, args.quiet)
        lp = args.log_path
        if args.subparser_name == constants.CONFIGURE:
            config = self.read_config(args.ini)
            config_validator(lv, lp).validate_minimal(config)
            configurer(config, log_level=lv, log_path=lp).run(args.out)
        elif args.subparser_name == constants.EXTRACT:
            config = self.read_config(args.ini)
            config_validator(lv, lp).validate_full(config)
            extractor(config, args.dir, log_level=lv, log_path=lp).run(args.json)
        elif args.subparser_name == constants.HTML:
            html_renderer(log_level=lv, log_path=lp).run(args.dir, args.html)
        elif args.subparser_name == constants.PDF:
            pdf_renderer(log_level=lv, log_path=lp).run(args.html, args.pdf)
        elif args.subparser_name == constants.ALL:
            config = self.read_config(args.ini)
            config_validator(lv, lp).validate_minimal(config)
            self.run_all(config, args, lv, lp)

    def run_all(self, input_config, args, log_level, log_path):
        """Run all Djerba operations in sequence"""
        with tempfile.TemporaryDirectory(prefix='djerba_all_') as tmp:
            ini_path_full = args.ini_out if args.ini_out else os.path.join(tmp, 'djerba_config_full.ini')
            html_path = args.html if args.html else os.path.join(tmp, 'djerba_report.html')
            if args.dir:
                report_dir = args.dir
            else:
                report_dir = os.path.join(tmp, 'report')
                os.mkdir(report_dir)
            configurer(input_config, log_level=log_level, log_path=log_path).run(ini_path_full)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
            # auto-generated full_config should be OK, but run the validator as a sanity check
            config_validator(log_level, log_path).validate_full(full_config)
            extractor(full_config, report_dir, log_level=log_level, log_path=log_path).run(args.json)
            html_renderer(log_level=log_level, log_path=log_path).run(report_dir, html_path)
            pdf_renderer(log_level=log_level, log_path=log_path).run(html_path, args.pdf)

    def validate_args(self, args):
        """Validate the command-line arguments"""
        v = path_validator()
        if args.log_path:
            v.validate_output_file(args.log_path)
        if args.subparser_name == constants.CONFIGURE:
            v.validate_input_file(args.ini)
            v.validate_output_file(args.out)
        elif args.subparser_name == constants.EXTRACT:
            v.validate_input_file(args.ini)
            v.validate_output_dir(args.dir)
            if args.json:
                v.validate_output_file(args.json)
        elif args.subparser_name == constants.HTML:
            v.validate_input_dir(args.dir)
            v.validate_output_file(args.html)
        elif args.subparser_name == constants.PDF:
            v.validate_input_file(args.html)
            v.validate_output_file(args.pdf)
        elif args.subparser_name == constants.ALL:
            v.validate_input_file(args.ini)
            v.validate_output_file(args.pdf)
            if args.ini_out:
                v.validate_output_file(args.ini_out)
            if args.dir:
                v.validate_output_dir(args.dir)
            if args.json:
                v.validate_output_file(args.json)
            if args.html:
                v.validate_output_file(args.html)
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: "+args.subparser_name)
    
