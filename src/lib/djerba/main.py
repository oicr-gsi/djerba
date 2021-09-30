"""Main class to run Djerba"""

import configparser
import getpass
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

    AUTHORS = {
        'afortuna': 'Alex Fortuna',
        'ibancarz': 'Iain Bancarz',
        'valamuri': 'Vivek Alamuri' # co-op student, autumn 2021
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

    def _get_analysis_unit(self):
        unit = None
        if self.args.unit:
            unit = self.args.unit
            self.logger.debug("Found analysis unit {0} from command-line args".format(unit))
        elif self.args.dir:
            unit_path = os.path.join(self.args.dir, constants.ANALYSIS_UNIT_FILENAME)
            self.logger.debug("Attempting to find analysis unit from file {0}".format(unit_path))
            path_validator(self.log_level).validate_input_file(unit_path)
            with open(unit_path) as unit_file:
                unit = unit_file.readline().strip() # read the first line, ignore others
            self.logger.debug("Found analysis unit {0} from file {1}".format(unit, unit_path))
        else:
            # shouldn't happen, but specify this for completeness
            err = "Must specify one of --unit or --dir to find analysis unit"
            self.logger.error(err)
            raise RuntimeError(err)
        return unit

    def _get_html_path(self):
        # find HTML path after running extractor, so we can access the analysis unit if needed
        if self.args.html:
            html_path = self.args.html
        else:
            html_path = os.path.join(self.args.dir, '{0}.html'.format(self._get_analysis_unit()))
        html_path = os.path.realpath(html_path) # needed to correctly render links
        self.logger.debug("Found HTML path {0}".format(html_path))
        return html_path

    def read_config(self, ini_path):
        """Read INI config from the given path"""
        ini_config = configparser.ConfigParser()
        ini_config.read(self.ini_defaults)
        ini_config.read(ini_path) # overwrites the defaults
        return ini_config

    def run(self):
        """Main method to run Djerba"""
        cv = config_validator(self.log_level, self.log_path)
        self.logger.info("Running Djerba in mode: {0}".format(self.args.subparser_name))
        if self.args.subparser_name == constants.SETUP:
            self.run_setup()
        elif self.args.subparser_name == constants.CONFIGURE:
            config = self.read_config(self.args.ini)
            cv.validate_minimal(config)
            archive = not self.args.no_archive # True if archiving is in effect
            configurer(config, self.log_level, self.log_path).run(self.args.out, archive)
        elif self.args.subparser_name == constants.EXTRACT:
            config = self.read_config(self.args.ini)
            cv.validate_full(config)
            extractor(config, self.args.dir, self.log_level, self.log_path).run(self.args.json)
        elif self.args.subparser_name == constants.HTML:
            if self.args.html:
                html_path = self.args.html
            else:
                html_path = os.path.join(self.args.dir, '{0}.html'.format(self._get_analysis_unit()))
            html_path = os.path.realpath(html_path) # needed to correctly render links
            hr = html_renderer(self.log_level, self.log_path)
            hr.run(self.args.dir, html_path, self.args.target_coverage, self.args.failed, self._get_author())
            if self.args.pdf:
                unit = self._get_analysis_unit()
                pdf_path = os.path.join(self.args.dir, "{0}.pdf".format(unit))
                pdf_renderer(self.log_level, self.log_path).run(html_path, pdf_path, unit)
        elif self.args.subparser_name == constants.PDF:
            unit = self._get_analysis_unit()
            pdf = os.path.join(self.args.dir, "{0}.pdf".format(unit))
            html_path = self._get_html_path()
            pdf_renderer(self.log_level, self.log_path).run(html_path, pdf, unit)
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
            json_path = os.path.realpath(self.args.json) if self.args.json else None
            report_dir = os.path.realpath(self.args.dir)
            archive = not self.args.no_archive # True if archiving is in effect
            configurer(input_config, self.log_level, self.log_path).run(ini_path_full, archive)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
            # auto-generated full_config should be OK, but run the validator as a sanity check
            config_validator(self.log_level, self.log_path).validate_full(full_config)
            extractor(full_config, report_dir, self.log_level, self.log_path).run(json_path)
            html_path = self._get_html_path()
            renderer = html_renderer(self.log_level, self.log_path)
            renderer.run(self.args.dir, html_path, self.args.target_coverage, self.args.failed, self._get_author())
            unit = self._get_analysis_unit()
            pdf = os.path.join(self.args.dir, "{0}.pdf".format(unit))
            pdf_renderer(self.log_level, self.log_path).run(self.args.html, pdf, unit)

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
            archive = not self.args.no_archive # True if archiving is in effect
            configurer(input_config, self.log_level, self.log_path).run(ini_path_full, archive)
            full_config = configparser.ConfigParser()
            full_config.read(ini_path_full)
            # auto-generated full_config should be OK, but run the validator as a sanity check
            config_validator(self.log_level, self.log_path).validate_full(full_config)
            extractor(full_config, report_dir, self.log_level, self.log_path).run(json_path)
            html_path = self._get_html_path()
            renderer = html_renderer(self.log_level, self.log_path)
            renderer.run(self.args.dir, html_path, self.args.target_coverage, self.args.failed, self._get_author())

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
            if args.json:
                v.validate_output_file(args.json)
        elif args.subparser_name == constants.HTML:
            v.validate_input_dir(args.dir)
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
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: "+args.subparser_name)
        self.logger.info("Command-line path validation finished.")
    
