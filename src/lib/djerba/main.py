"""Main class to run Djerba"""

import configparser
import getpass
import json
import logging
import os
import re
import tempfile
from shutil import copyfile

import djerba.render.constants as rc
import djerba.util.constants as constants
from djerba import __version__
from djerba.configure import configurer
from djerba.extract.extractor import extractor
from djerba.render.render import html_renderer
from djerba.render.render import pdf_renderer
from djerba.util.logger import logger
from djerba.util.validator import config_validator, path_validator

class main(logger):

    """Main class to run Djerba"""

    AUTHORS = {
        'afortuna': 'Alex Fortuna',
        'ibancarz': 'Iain Bancarz',
        'fbeaudry': 'Felix Beaudry',
        'wytong': 'Wen Tong'
    }
    CONFIG_NAME = 'config.ini'
    INI_DEFAULT_NAME = 'defaults.ini'
    INI_TEMPLATE_NAME = 'config_template.ini'
    REPORT_SUBDIR_NAME = 'report'
    
    def __init__(self, args):
        source_dir = os.path.dirname(os.path.realpath(__file__))
        self.ini_defaults = os.path.join(source_dir, constants.DATA_DIR_NAME, self.INI_DEFAULT_NAME)
        self.ini_template = os.path.join(source_dir, constants.DATA_DIR_NAME, self.INI_TEMPLATE_NAME)
        self.args = args
        if self.args.subparser_name in [constants.SETUP, constants.PDF]:
            self.failed = False # --failed option not relevant for these modes
            self.wgs_only = False # similarly for wgs-only
        else:
            self.failed = self.args.failed
            self.wgs_only = self.args.wgs_only
        self.log_level = self.get_args_log_level(self.args)
        self.log_path = self.args.log_path
        if self.log_path:
            # we are verifying the log path, so don't write output there yet
            path_validator(self.log_level).validate_output_file(self.log_path)
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.logger.info("Running Djerba version {0}".format(__version__))
        self.validate_args(args) # checks subparser and args are valid

    def _get_author(self):
        """Find the author name. If not in args, try to find from the username; otherwise use default"""
        # author is not an INI parameter, because an INI file is not used in HTML mode
        username = getpass.getuser()
        if self.args.author:
            author = self.args.author
            self.logger.debug("Using author '{0}' from command line".format(author))
        elif username in self.AUTHORS:
            author = self.AUTHORS[username]
            self.logger.debug("Found author '{0}' from username {1}".format(author, username))
        else:
            author = "user {0}".format(username)
            msg = "Author name not known, falling back to '{0}'".format(author)
            self.logger.warning(msg)
        return author

    def _get_html_path(self, report_id=None):
        if self.args.html:
            html_path = self.args.html
        elif report_id and self.args.dir:
            html_path = os.path.join(self.args.dir, '{0}_report.html'.format(report_id))
        else:
            msg = "Must specify --html, or --dir and a report ID, to find HTML output path"
            self.logger.error(msg)
            raise RuntimeError(msg)
        html_path = os.path.realpath(html_path) # needed to correctly render links
        self.logger.debug("Found HTML path {0}".format(html_path))
        return html_path

    def _get_json_path(self):
        # get JSON input path from args
        if self.args.json:
            json_path = os.path.realpath(self.args.json)
        elif self.args.dir:
            json_path = os.path.join(self.args.dir, constants.REPORT_JSON_FILENAME)
        else:
            msg = "Must specify --json or --dir to find JSON input path"
            self.logger.error(msg)
            raise RuntimeError(msg)
        json_path = os.path.realpath(json_path)
        self.logger.debug("Found JSON path {0}".format(json_path))
        return json_path

    def _get_pdf_path(self, report_id):
        """Get PDF path for given report ID string"""
        pdf_path = os.path.join(self.args.dir, '{0}_report.pdf'.format(report_id))
        pdf_path = os.path.realpath(pdf_path)
        self.logger.debug("Found PDF path {0}".format(pdf_path))
        return pdf_path

    def _get_report_id_from_html(self, html_path):
        # simple but adequate method; report ID derived from HTML filename
        items0 = re.split('\.', os.path.basename(html_path))
        items0.pop() # remove the .html suffix
        name0 = '.'.join(items0)
        items1 = re.split('_', name0)
        items1.pop() # remove the _report suffix
        report_id = '_'.join(items1)
        return report_id

    def _get_report_id_from_json(self, json_path):
        with open(json_path) as json_file:
            data = json.loads(json_file.read())
            report_id = data[constants.REPORT][rc.PATIENT_INFO][rc.REPORT_ID]
        return report_id

    def read_config(self, ini_path):
        """Read INI config from the given path"""
        ini_config = configparser.ConfigParser()
        ini_config.read(self.ini_defaults)
        ini_config.read(ini_path) # overwrites the defaults
        return ini_config

    def run(self):
        """Main method to run Djerba"""
        # don't use self.args.failed or self.args.wgs_only -- not defined for some subparsers
        cv = config_validator(self.wgs_only, self.failed, self.log_level, self.log_path)
        self.logger.info("Running Djerba in mode: {0}".format(self.args.subparser_name))
        if self.args.subparser_name == constants.SETUP:
            self.run_setup()
        elif self.args.subparser_name == constants.CONFIGURE:
            config = self.read_config(self.args.ini)
            cv.validate_minimal(config)
            configurer(config, self.wgs_only, self.args.failed, self.log_level, self.log_path).run(self.args.out)
        elif self.args.subparser_name == constants.EXTRACT:
            config = self.read_config(self.args.ini)
            cv.validate_full(config)
            extractor(config, self.args.dir, self._get_author(), self.wgs_only, self.args.target_coverage, self.args.failed, self.args.target_coverage, self.log_level, self.log_path).run()
        elif self.args.subparser_name == constants.HTML:
            json_path = self._get_json_path()
            report_id = self._get_report_id_from_json(json_path)
            html_path = self._get_html_path(report_id)
            archive = not self.args.no_archive
            html_renderer(self.log_level, self.log_path).run(json_path, html_path, archive)
            if self.args.pdf:
                pdf_path = self._get_pdf_path(report_id)
                pdf_renderer(self.log_level, self.log_path).run(html_path, pdf_path, report_id)
        elif self.args.subparser_name == constants.PDF:
            html_path = self.args.html
            if self.args.report_id:
                report_id = self.args.report_id
            else:
                report_id = self._get_report_id_from_html(html_path)
            pdf_path = self._get_pdf_path(report_id)
            pdf_renderer(self.log_level, self.log_path).run(html_path, pdf_path, report_id)
        elif self.args.subparser_name == constants.DRAFT:
            config = self.read_config(self.args.ini)
            cv.validate_minimal(config)
            self.run_draft(config)
        elif self.args.subparser_name == constants.ALL:
            config = self.read_config(self.args.ini)
            cv.validate_minimal(config)
            self.run_all(config)
        else:
            msg = "Unknown subparser name {0}".format(self.args.subparser_name)
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.logger.info("Finished running Djerba in mode: {0}".format(self.args.subparser_name))

    def run_all(self, input_config):
        """Run all Djerba operations in sequence"""
        with tempfile.TemporaryDirectory(prefix='djerba_all_') as tmp:
            ini_path_full = self.args.ini_out if self.args.ini_out else os.path.join(tmp, 'djerba_config_full.ini')
            report_dir = os.path.realpath(self.args.dir)
            configurer(input_config, self.args.wgs_only, self.args.failed, self.log_level, self.log_path).run(ini_path_full)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
            # auto-generated full_config should be OK, but run the validator as a sanity check
            config_validator(self.args.wgs_only, self.args.failed, self.log_level, self.log_path).validate_full(full_config)
            extractor(full_config, report_dir, self._get_author(), self.args.wgs_only, self.args.failed, self.args.target_coverage, self.log_level, self.log_path).run()
            json_path = os.path.join(self.args.dir, constants.REPORT_JSON_FILENAME)
            report_id = self._get_report_id_from_json(json_path)
            html_path = self._get_html_path(report_id)
            archive = not self.args.no_archive
            html_renderer(self.log_level, self.log_path).run(json_path, html_path, archive)
            pdf = self._get_pdf_path(report_id)
            pdf_renderer(self.log_level, self.log_path).run(self.args.html, pdf, report_id)

    def run_draft(self, input_config):
        """
        Run Djerba operations up to and including HTML; do not render PDF
        Reporting directory and HTML paths are required
        """
        with tempfile.TemporaryDirectory(prefix='djerba_draft_') as tmp:
            ini_path_full = self.args.ini_out if self.args.ini_out else os.path.join(tmp, 'djerba_config_full.ini')
            if self.args.dir:
                report_dir = os.path.realpath(self.args.dir)
            else:
                msg = "Report directory path is required in {0} mode".format(constants.DRAFT)
                self.logger.error(msg)
                raise ValueError(msg)
            configurer(input_config, self.args.wgs_only, self.args.failed, self.log_level, self.log_path).run(ini_path_full)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
            # auto-generated full_config should be OK, but run the validator as a sanity check
            config_validator(self.args.wgs_only, self.args.failed, self.log_level, self.log_path).validate_full(full_config)
            extractor(full_config, report_dir, self._get_author(), self.args.wgs_only, self.args.failed, self.args.target_coverage, self.log_level, self.log_path).run()
            json_path = os.path.join(self.args.dir, constants.REPORT_JSON_FILENAME)
            html_path = self._get_html_path(self._get_report_id_from_json(json_path))
            archive = not self.args.no_archive
            html_renderer(self.log_level, self.log_path).run(json_path, html_path, archive)

    def run_setup(self):
        """Set up an empty working directory for a CGI report"""
        working_dir_path = os.path.join(self.args.base, self.args.name)
        self.logger.info("Setting up working directory in {0}".format(working_dir_path))
        os.mkdir(working_dir_path)
        os.mkdir(os.path.join(working_dir_path, self.REPORT_SUBDIR_NAME))
        os.mkdir(os.path.join(working_dir_path, constants.MAVIS_SUBDIR_NAME))
        config_dest = os.path.join(working_dir_path, self.CONFIG_NAME)
        copyfile(self.ini_template, config_dest)
        self.logger.info("Finished setting up working directory")

    def validate_args(self, args):
        """Check we can read/write paths in command-line arguments"""
        self.logger.info("Validating paths in command-line arguments")
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
        elif args.subparser_name == constants.HTML:
            if args.dir:
                v.validate_input_dir(args.dir)
            if args.json:
                v.validate_input_file(args.json)
            if args.html:
                v.validate_output_file(args.html)
        elif args.subparser_name == constants.PDF:
            v.validate_input_file(args.html)
            v.validate_output_dir(args.dir)
        elif args.subparser_name == constants.DRAFT:
            v.validate_input_file(args.ini)
            v.validate_output_dir(args.dir)
            if args.html:
                v.validate_output_file(args.html)
            if args.ini_out:
                v.validate_output_file(args.ini_out)
        elif args.subparser_name == constants.ALL:
            v.validate_input_file(args.ini)
            if args.ini_out:
                v.validate_output_file(args.ini_out)
            if args.dir:
                v.validate_output_dir(args.dir)
            if args.html:
                v.validate_output_file(args.html)
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: "+args.subparser_name)
        self.logger.info("Command-line path validation finished.")
