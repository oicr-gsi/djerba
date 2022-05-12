"""Main class to run Djerba"""

import configparser
import getpass
import logging
import os
import re
import tempfile
from shutil import copyfile

import djerba.util.constants as constants
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
        'fbeaudry': 'Felix Beaudry'
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
        else:
            self.failed = self.args.failed
        self.log_level = self.get_log_level(self.args.debug, self.args.verbose, self.args.quiet)
        self.log_path = self.args.log_path
        if self.log_path:
            # we are verifying the log path, so don't write output there yet
            path_validator(self.log_level).validate_output_file(self.log_path)
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
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

    def _get_html_path(self):
        # find HTML path after running extractor, so we can access the clinical data path if needed
        if self.args.html:
            html_path = self.args.html
        elif self.args.dir:
            patient_id = self._get_patient_study_id(self.args.dir)
            html_path = os.path.join(self.args.dir, '{0}_djerba_report.html'.format(patient_id))
        else:
            msg = "Must specify --html or --dir to find HTML output path"
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
            json_path = os.path.join(self.args.dir, constants.REPORT_MACHINE_FILENAME)
        else:
            msg = "Must specify --json or --dir to find JSON input path"
            self.logger.error(msg)
            raise RuntimeError(msg)
        json_path = os.path.realpath(json_path)
        self.logger.debug("Found JSON path {0}".format(json_path))
        return json_path

    def _get_patient_study_id(self, input_dir):
        """Read patient LIMS ID from data_clinical.txt file, for constructing filenames"""
        clinical_data = self._read_clinical_data_fields(input_dir)
        lims_id = clinical_data[constants.PATIENT_STUDY_ID]
        self.logger.debug("Found patient study ID: {0}".format(lims_id))
        return lims_id

    def _get_pdf_path(self, patient_id):
        """Get PDF path for given patient ID string"""
        pdf_path = os.path.join(self.args.dir, '{0}_djerba_report.pdf'.format(patient_id))
        pdf_path = os.path.realpath(pdf_path)
        self.logger.debug("Found PDF path {0}".format(pdf_path))
        return pdf_path

    def _read_clinical_data_fields(self, input_dir):
        """Read the clinical data TSV into a dictionary"""
        input_path = os.path.join(input_dir, constants.CLINICAL_DATA_FILENAME)
        path_validator(self.log_level, self.log_path).validate_input_file(input_path)
        with open(input_path) as input_file:
            input_lines = input_file.readlines()
        # first sanity check
        if not (len(input_lines)==2 and re.match(constants.PATIENT_LIMS_ID, input_lines[0])):
            msg = "Incorrect format in clinical data file at {0}".format(input_path)
            self.logger.error(msg)
            raise ValueError(msg)
        head = re.split("\t", input_lines[0].strip())
        body = re.split("\t", input_lines[1].strip())
        # second sanity check
        if len(head)!=len(body):
            msg = "Mismatched header and body fields in {0}".format(input_path)
            self.logger.error(msg)
            raise ValueError(msg)
        clinical_data = {head[i]:body[i] for i in range(len(head))}
        return clinical_data

    def read_config(self, ini_path):
        """Read INI config from the given path"""
        ini_config = configparser.ConfigParser()
        ini_config.read(self.ini_defaults)
        ini_config.read(ini_path) # overwrites the defaults
        return ini_config

    def run(self):
        """Main method to run Djerba"""
        # don't use self.args.failed -- it is not defined for some subparsers
        cv = config_validator(self.args.wgs_only, self.failed, self.log_level, self.log_path)
        self.logger.info("Running Djerba in mode: {0}".format(self.args.subparser_name))
        if self.args.subparser_name == constants.SETUP:
            self.run_setup()
        elif self.args.subparser_name == constants.CONFIGURE:
            config = self.read_config(self.args.ini)
            cv.validate_minimal(config)
            configurer(config, self.args.wgs_only, self.args.failed, self.log_level, self.log_path).run(self.args.out)
        elif self.args.subparser_name == constants.EXTRACT:
            config = self.read_config(self.args.ini)
            cv.validate_full(config)
            extractor(config, self.args.dir, self._get_author(), self.args.wgs_only, self.args.target_coverage, self.args.failed, self.args.target_coverage, self.log_level, self.log_path).run()
        elif self.args.subparser_name == constants.HTML:
            json_path = self._get_json_path()
            html_path = self._get_html_path()
            archive = not self.args.no_archive
            html_renderer(self.log_level, self.log_path).run(json_path, html_path, archive)
            if self.args.pdf:
                patient_id = self._get_patient_study_id(self.args.dir)
                pdf_path = self._get_pdf_path(patient_id)
                pdf_renderer(self.log_level, self.log_path).run(html_path, pdf_path, patient_id)
        elif self.args.subparser_name == constants.PDF:
            html_path = self._get_html_path()
            patient_id = self._get_patient_study_id(self.args.dir)
            pdf_path = self._get_pdf_path(patient_id)
            pdf_renderer(self.log_level, self.log_path).run(html_path, pdf_path, patient_id)
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
            html_path = self._get_html_path()
            json_path = os.path.join(self.args.dir, constants.REPORT_MACHINE_FILENAME)
            archive = not self.args.no_archive
            html_renderer(self.log_level, self.log_path).run(json_path, html_path, archive)
            patient_id = self._get_patient_study_id(self.args.dir)
            pdf = self._get_pdf_path(patient_id)
            pdf_renderer(self.log_level, self.log_path).run(self.args.html, pdf, patient_id)

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
            html_path = self._get_html_path()
            json_path = os.path.join(self.args.dir, constants.REPORT_MACHINE_FILENAME)
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
            v.validate_output_dir(args.dir)
            if args.html:
                v.validate_input_file(args.html)
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
