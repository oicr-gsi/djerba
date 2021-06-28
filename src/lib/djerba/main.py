"""Main class to run Djerba"""

import configparser
import os
import tempfile

import djerba.util.constants as constants
from djerba.configure import configurer
from djerba.extract import extractor
from djerba.render import html_renderer
from djerba.render import pdf_renderer
from djerba.util.validator import validator

class main:

    """Main class to run Djerba"""
    
    INI_DEFAULT_NAME = 'defaults.ini'
    
    def __init__(self):
        source_dir = os.path.dirname(os.path.realpath(__file__))
        self.ini_defaults = os.path.join(source_dir, constants.DATA_DIR_NAME, self.INI_DEFAULT_NAME)

    def run(self, args):
        """Main method to run Djerba"""
        self.validate_args(args)
        ini_config = configparser.ConfigParser()
        ini_config.read(self.ini_defaults)
        ini_config.read(args.ini) # overwrites the defaults
        if args.subparser_name == constants.CONFIGURE:
            configurer(ini_config).run(args.out)
        elif args.subparser_name == constants.EXTRACT:
            extractor(ini_config, args.dir).run(args.json)
        elif args.subparser_name == constants.HTML:
            html_renderer(ini_config, args.dir).run(args.html)
        elif args.subparser_name == constants.PDF:
            pdf_renderer(ini_config).run(args.html, args.pdf)
        elif args.subparser_name == constants.ALL:
            self.run_all(args)

    def run_all(self, args):
        """Run all Djerba operations in sequence"""
        with tempfile.TemporaryDirectory(prefix='djerba_all_') as tmp:
            ini_full = args.config if args.config else os.path.join(tmp, 'djerba_config_full.ini')
            html_path = args.html if args.html else os.path.join(tmp, 'djerba_report.html')
            if args.dir:
                report_dir = args.dir
            else:
                report_dir = os.path.join(tmp, 'report')
                os.mkdir(report_dir)
            configurer(ini_config).run(ini_full)
            extractor(ini_full, report_dir).run(args.json)
            html_renderer(ini_full).run(report_dir, html_path)
            pdf_renderer(ini_full).run(html_path, args.pdf)

    def validate_args(self, args):
        """Validate the command-line arguments"""
        v = validator()
        v.validate_input_file(args.ini)
        if args.subparser_name == self.CONFIGURE:
            v.validate_output_file(args.out)
        elif args.subparser_name == self.EXTRACT:
            v.validate_output_dir(args.dir)
            if args.json:
                v.validate_output_file(args.json)
        elif args.subparser_name == self.HTML:
            v.validate_input_dir(args.dir)
            v.validate_output_file(args.html)
        elif args.subparser_name == self.PDF:
            v.validate_input_file(args.html)
            v.validate_output_file(args.pdf)
        elif args.subparser_name == self.ALL:
            v.validate_output_file(args.pdf)
            if args.config:
                v.validate_output_file(args.config)
            if args.dir:
                v.validate_output_dir(args.dir)
            if args.json:
                v.validate_output_file(args.json)
            if args.html:
                v.validate_output_file(args.html)
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: "+args.subparser_name)
    
