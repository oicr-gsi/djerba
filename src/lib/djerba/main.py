"""Main class to run Djerba"""

import configparser
import logging
import os
import tempfile
from shutil import copyfile

import djerba.util.constants as constants
from djerba.configure import configurer
from djerba.extract.extractor import extractor
from djerba.render import html_renderer
from djerba.render import pdf_renderer
from djerba.util.logger import logger
from djerba.util.validator import config_validator, path_validator

class main(logger):

    """Main class to run Djerba"""

    CONFIG_NAME = 'config.ini'
    INI_DEFAULT_NAME = 'defaults.ini'
    INI_TEMPLATE_NAME = 'config_template.ini'
    REPORT_SUBDIR_NAME = 'report'
    
    def __init__(self, args):
        source_dir = os.path.dirname(os.path.realpath(__file__))
        self.ini_defaults = os.path.join(source_dir, constants.DATA_DIR_NAME, self.INI_DEFAULT_NAME)
        self.ini_template = os.path.join(source_dir, constants.DATA_DIR_NAME, self.INI_TEMPLATE_NAME)
        self.args = args
        self.log_level = self.get_log_level(self.args.debug, self.args.verbose, self.args.quiet)
        self.log_path = self.args.log_path
        if self.log_path:
            # we are verifying the log path, so don't write output there yet
            path_validator(self.log_level).validate_output_file(self.log_path)
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.validate_args(args) # checks subparser and args are valid

    def _get_pdf_path(self):
        if self.args.pdf:
            pdf_path = self.args.pdf
        elif self.args.pdf_dir and self.args.unit:
            name = "{0}.pdf".format(self.args.unit)
            pdf_path = os.path.join(self.args.pdf_dir, name)
        else:
            msg = "Must specify either a PDF output path, or a directory and analysis unit"
            self.logger.error(msg)
            raise RuntimeError(msg)
        return pdf_path

    def read_config(self, ini_path):
        """Read INI config from the given path"""
        ini_config = configparser.ConfigParser()
        ini_config.read(self.ini_defaults)
        ini_config.read(ini_path) # overwrites the defaults
        return ini_config

    def run(self):
        """Main method to run Djerba"""
        cv = config_validator(self.log_level, self.log_path)
        if self.args.subparser_name == constants.SETUP:
            self.run_setup()
        elif self.args.subparser_name == constants.CONFIGURE:
            config = self.read_config(self.args.ini)
            cv.validate_minimal(config)
            configurer(config, self.log_level, self.log_path).run(self.args.out)
        elif self.args.subparser_name == constants.EXTRACT:
            config = self.read_config(self.args.ini)
            cv.validate_full(config)
            extractor(config, self.args.dir, self.log_level, self.log_path).run(self.args.json)
        elif self.args.subparser_name == constants.HTML:
            html_path = os.path.realpath(self.args.html) # needed to correctly render links
            renderer = html_renderer(self.log_level, self.log_path)
            renderer.run(self.args.dir, html_path, self.args.target_coverage, self.args.failed)
        elif self.args.subparser_name == constants.PDF:
            pdf = self._get_pdf_path()
            if self.args.no_footer:
                pdf_renderer(self.log_level, self.log_path).run(self.args.html, pdf, footer=False)
            else:
                pdf_renderer(self.log_level, self.log_path).run(self.args.html, pdf, self.args.unit)
        elif self.args.subparser_name == constants.DRAFT:
            config = self.read_config(self.args.ini)
            cv.validate_minimal(config)
            self.run_draft(config)
        elif self.args.subparser_name == constants.ALL:
            config = self.read_config(self.args.ini)
            cv.validate_minimal(config)
            self.run_all(config)

    def run_all(self, input_config):
        """Run all Djerba operations in sequence"""
        with tempfile.TemporaryDirectory(prefix='djerba_all_') as tmp:
            ini_path_full = self.args.ini_out if self.args.ini_out else os.path.join(tmp, 'djerba_config_full.ini')
            # *must* use absolute HTML path to render links correctly in Rmarkdown
            html_path = os.path.realpath(self.args.html) if self.args.html else os.path.join(tmp, 'djerba_report.html')
            json_path = os.path.realpath(self.args.json) if self.args.json else None
            if self.args.dir:
                report_dir = os.path.realpath(self.args.dir)
            else:
                report_dir = os.path.join(tmp, 'report')
                os.mkdir(report_dir)
            configurer(input_config, self.log_level, self.log_path).run(ini_path_full)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
            # auto-generated full_config should be OK, but run the validator as a sanity check
            config_validator(self.log_level, self.log_path).validate_full(full_config)
            extractor(full_config, report_dir, self.log_level, self.log_path).run(json_path)
            renderer = html_renderer(self.log_level, self.log_path)
            renderer.run(self.args.dir, html_path, self.args.target_coverage, self.args.failed)
            pdf = self._get_pdf_path()
            pdf_renderer(self.log_level, self.log_path).run(html_path, pdf, self.args.unit)

    def run_draft(self, input_config):
        """
        Run Djerba operations up to and including HTML; do not render PDF
        Reporting directory and HTML paths are required
        """
        with tempfile.TemporaryDirectory(prefix='djerba_draft_') as tmp:
            ini_path_full = self.args.ini_out if self.args.ini_out else os.path.join(tmp, 'djerba_config_full.ini')
            json_path = os.path.realpath(self.args.json) if self.args.json else None
            if self.args.dir:
                report_dir = os.path.realpath(self.args.dir)
            else:
                msg = "Report directory path is required in {0} mode".format(constants.DRAFT)
                self.logger.error(msg)
                raise ValueError(msg)
            if self.args.html:
                # *must* use absolute HTML path to render links correctly in Rmarkdown
                html_path = os.path.realpath(self.args.html)
            else:
                msg = "HTML path is required in {0} mode".format(constants.DRAFT)
                self.logger.error(msg)
                raise ValueError(msg)
            configurer(input_config, self.log_level, self.log_path).run(ini_path_full)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
            # auto-generated full_config should be OK, but run the validator as a sanity check
            config_validator(self.log_level, self.log_path).validate_full(full_config)
            extractor(full_config, report_dir, self.log_level, self.log_path).run(json_path)
            renderer = html_renderer(self.log_level, self.log_path)
            renderer.run(self.args.dir, html_path, self.args.target_coverage, self.args.failed)

    def run_setup(self):
        """Set up an empty working directory for a CGI report"""
        working_dir_path = os.path.join(self.args.base, self.args.name)
        self.logger.info("Setting up working directory in {0}".format(working_dir_path))
        os.mkdir(working_dir_path)
        os.mkdir(os.path.join(working_dir_path, self.REPORT_SUBDIR_NAME))
        config_dest = os.path.join(working_dir_path, self.CONFIG_NAME)
        copyfile(self.ini_template, config_dest)
        self.logger.info("Finished setting up working directory")

    def validate_args(self, args):
        """Validate the command-line arguments"""
        v = path_validator(self.log_level, self.log_path)
        if args.log_path:
            v.validate_output_file(args.log_path)
        if args.subparser_name == constants.SETUP:
            v.validate_output_dir(args.base)
        elif args.subparser_name == constants.CONFIGURE:
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
            if args.pdf:
                v.validate_output_file(args.pdf)
            elif args.pdf_dir: # --pdf overrides --pdf-dir
                v.validate_output_dir(args.pdf_dir)
        elif args.subparser_name == constants.DRAFT:
            v.validate_input_file(args.ini)
            v.validate_output_dir(args.dir)
            v.validate_output_file(args.html)
            if args.ini_out:
                v.validate_output_file(args.ini_out)
            if args.json:
                v.validate_output_file(args.json)
        elif args.subparser_name == constants.ALL:
            v.validate_input_file(args.ini)
            if args.ini_out:
                v.validate_output_file(args.ini_out)
            if args.dir:
                v.validate_output_dir(args.dir)
            if args.json:
                v.validate_output_file(args.json)
            if args.html:
                v.validate_output_file(args.html)
            if args.pdf:
                v.validate_output_file(args.pdf)
            elif args.pdf_dir: # --pdf overrides --pdf-dir
                v.validate_output_dir(args.pdf_dir)
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: "+args.subparser_name)
    
