"""Main class to run Djerba"""

import configparser
import getpass
import json
import os
import re
import tempfile
from shutil import copyfile

import djerba.render.constants as rc
import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba import __version__
from djerba.configure import configurer
from djerba.extract.extractor import extractor
from djerba.extract.oncokb.cache import oncokb_cache_params
from djerba.render.render import html_renderer, pdf_renderer
from djerba.util.logger import logger
from djerba.util.validator import config_validator, path_validator


class main(logger):
    """Main class to run Djerba"""

    AUTHORS = {
        'afortuna': 'Alex Fortuna',
        'ibancarz': 'Iain Bancarz',
        'fbeaudry': 'Felix Beaudry',
        'aalam': 'Aqsa Alam'
    }
    CONFIG_NAME = 'config.ini'
    INI_DEFAULT_NAME = 'defaults.ini'
    INI_TEMPLATE_NAME = 'config_template.ini'
    REPORT_SUBDIR_NAME = 'report'

    def __init__(self, args):
        super().__init__()
        source_dir = os.path.dirname(os.path.realpath(__file__))
        self.ini_defaults = os.path.join(source_dir, constants.DATA_DIR_NAME, self.INI_DEFAULT_NAME)
        self.ini_template = os.path.join(source_dir, constants.DATA_DIR_NAME, self.INI_TEMPLATE_NAME)
        self.args = args
        if self.args.subparser_name in [constants.SETUP, constants.PDF]:
            self.failed = False  # --failed option not relevant for these modes
            self.wgs_only = False  # similarly for wgs-only
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
        self.validate_args(args)  # checks subparser and args are valid

    def _build_cache_params(self, config):
        """Build oncoKB cache parameters for the extractor"""
        params = oncokb_cache_params(
            config.get(ini.SETTINGS, ini.ONCOKB_CACHE),
            self.args.apply_cache,
            self.args.update_cache,
            log_level=self.log_level,
            log_path=self.log_path
        )
        self.logger.debug("OncoKB cache params: {0}".format(params))
        return params

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
    
    def _get_html_path(self,report_id,is_clinical):
        if(is_clinical == True):       
            out_file_suffix = constants.CLINICAL_HTML_SUFFIX
        elif (is_clinical == False):
            out_file_suffix = constants.RESEARCH_HTML_SUFFIX  
        html_path = os.path.realpath(os.path.join(self.args.dir, report_id + out_file_suffix))
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

    @staticmethod
    def _get_pdf_prefix(report_id):
        return report_id+'_report'

    @staticmethod
    def _get_report_id_from_html(html_path):
        # simple but adequate method; report ID derived from HTML filename
        items0 = re.split('\.', os.path.basename(html_path))
        items0.pop()  # remove the .html suffix
        name0 = '.'.join(items0)
        items1 = re.split('_', name0)
        items1.pop()  # remove the _report suffix
        report_id = '_'.join(items1)
        return report_id

    @staticmethod
    def _get_report_id_from_json(json_path):
        with open(json_path) as json_file:
            data = json.loads(json_file.read())
            report_id = data[constants.REPORT][rc.PATIENT_INFO][rc.REPORT_ID]
        return report_id

    def read_config(self, ini_path):
        """Read INI config from the given path"""
        ini_config = configparser.ConfigParser()
        ini_config.read(self.ini_defaults)
        ini_config.read(ini_path)  # overwrites the defaults
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
            cleanup = not self.args.no_cleanup
            extractor(config, self.args.dir, self._get_author(), self.wgs_only, self.args.failed, 
                      self._build_cache_params(config), cleanup, self.log_level,
                      self.log_path).run()
        elif self.args.subparser_name == constants.HTML:
            json_path = self._get_json_path()
            report_id = self._get_report_id_from_json(json_path)
            archive = not self.args.no_archive
            hr = html_renderer(self.log_level, self.log_path)
            html_clinical = hr.run_clinical(json_path, self.args.dir, report_id, archive)
            html_research = hr.run_research(json_path, self.args.dir, report_id, archive=False)
            if self.args.pdf:
                pdf_renderer(self.log_level, self.log_path).run_all(
                    html_clinical,
                    html_research,
                    self.args.dir,
                    self._get_pdf_prefix(report_id),
                    report_id
                )
        elif self.args.subparser_name == constants.PDF:
            dir_path = self.args.dir
            json_path = self._get_json_path()
            report_id = self._get_report_id_from_json(json_path)
            html_clinical = self._get_html_path(report_id, True)
            html_research = self._get_html_path(report_id, False)
            pdf_renderer(self.log_level, self.log_path).run_all(
                html_clinical,
                html_research,
                dir_path,
                self._get_pdf_prefix(report_id),
                report_id
            )
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
            configurer(input_config, self.args.wgs_only, self.args.failed, self.log_level, self.log_path).run(
                ini_path_full)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
        # auto-generated full_config should be OK, but run the validator as a sanity check
        config_validator(self.args.wgs_only, self.args.failed, self.log_level, self.log_path).validate_full(full_config)
        cache_params = self._build_cache_params(full_config)
        cleanup = not self.args.no_cleanup
        extractor(full_config, report_dir, self._get_author(), self.args.wgs_only, self.args.failed,
                  cache_params, cleanup, self.log_level, self.log_path).run()
        json_path = os.path.join(self.args.dir, constants.REPORT_JSON_FILENAME)
        report_id = self._get_report_id_from_json(json_path)
        archive = not self.args.no_archive
        hr = html_renderer(self.log_level, self.log_path)
        html_clinical = hr.run_clinical(json_path, self.args.dir, report_id, archive)
        html_research = hr.run_research(json_path, self.args.dir, report_id, archive=False)
        pdf_renderer(self.log_level, self.log_path).run_all(
            html_clinical,
            html_research,
            self.args.dir,
            self._get_pdf_prefix(report_id),
            report_id
        )

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
            configurer(input_config, self.args.wgs_only, self.args.failed, self.log_level, self.log_path).run(
                ini_path_full)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
            # auto-generated full_config should be OK, but run the validator as a sanity check
            config_validator(self.args.wgs_only, self.args.failed, self.log_level, self.log_path).validate_full(
                full_config)
            cache_params = self._build_cache_params(full_config)
            cleanup = not self.args.no_cleanup
            extractor(full_config, report_dir, self._get_author(), self.args.wgs_only, self.args.failed,
                       cache_params, cleanup, self.log_level, self.log_path).run()
            json_path = os.path.join(self.args.dir, constants.REPORT_JSON_FILENAME)
            report_id = self._get_report_id_from_json(json_path)
            archive = not self.args.no_archive
            hr = html_renderer(self.log_level, self.log_path)
            html_clinical = hr.run_clinical(json_path, self.args.dir, report_id, archive)
            html_research = hr.run_research(json_path, self.args.dir, report_id, archive=False)

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
        elif args.subparser_name == constants.PDF:
            v.validate_input_file(args.json)
            v.validate_output_dir(args.dir)
        elif args.subparser_name == constants.DRAFT:
            v.validate_input_file(args.ini)
            v.validate_output_dir(args.dir)
            if args.ini_out:
                v.validate_output_file(args.ini_out)
        elif args.subparser_name == constants.ALL:
            v.validate_input_file(args.ini)
            if args.ini_out:
                v.validate_output_file(args.ini_out)
            if args.dir:
                v.validate_output_dir(args.dir)
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: " + args.subparser_name)
        self.logger.info("Command-line path validation finished.")
