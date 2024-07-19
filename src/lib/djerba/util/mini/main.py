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
from djerba.util.date import get_todays_date, is_valid_date
from djerba.util.logger import logger
from djerba.util.validator import path_validator
from djerba.version import get_djerba_version

class main(main_base):

    INI_FILENAME = 'mini_djerba.ini'
    PATIENT_INFO = 'patient_info'
    SUPPLEMENT = 'supplement.body'
    SUMMARY = 'summary'
    SUMMARY_FILENAME = 'summary.txt'
    SUMMARY_DEFAULT = 'Patient summary text; not in use for PWGS'
    SUPPLEMENT_KEYS = [
        supplement_plugin.REPORT_SIGNOFF_DATE,
        supplement_plugin.GENETICIST,
        supplement_plugin.GENETICIST_ID
    ]

    def has_summary(self, data):
        # some reports do not have a summary, eg. PWGS
        return self.SUMMARY in data[cc.PLUGINS]

    def run(self, args):
        """
        Process command-line args and run 'setup', 'render' or 'update'
        """
        ap = arg_processor(args, self.logger, validate=False)
        mode = ap.get_mode()
        if mode == constants.SETUP:
            self.setup(
                ap.get_out_dir(),
                ap.get_json()
            )
        elif mode == constants.REPORT:
            self.report(
                ap.get_json(),
                ap.get_out_dir(),
                ap.is_forced(),
                ap.is_pdf_enabled(),
                ap.get_ini_path(),
                ap.get_summary_path()
            )
        else:
            msg = "Mode '{0}' is not defined in Djerba mini.main!".format(mode)
            self.logger.error(msg)
            raise RuntimeError(msg)

    def report(self, json_path, out_dir, force, pdf, ini_path=None, summary_path=None):
        """
        Generate a report (with optional updates); replaces render and update modes
        Required: JSON input path, out_dir
        Optional: Patient info INI path, summary text path, force boolean, pdf boolean

        If given, INI path is validated to contain exactly the parameters needed
        Update is carried out using the HTML cache in JSON
        """
        with open(json_path) as in_file:
            data = json.loads(in_file.read())
        doc_key = self._get_unique_doc_key(data)
        if ini_path or summary_path:
            # update data for the given parameters
            config = ConfigParser()
            if ini_path:
                self.validate_ini(ini_path)
                config.read(ini_path)
            # set the assay
            try:
                assay = data[cc.CONFIG][constants.SUPPLEMENTARY]['assay']
            except KeyError as err:
                msg = "Cannot find Djerba assay from input JSON: {0}".format(err)
                self.logger.error(msg)
                raise MiniDjerbaScriptError(msg) from err
            config.set(constants.SUPPLEMENTARY, 'assay', assay)
            if summary_path:
                if self.has_summary(data):
                    config.add_section(constants.SUMMARY)
                    config.set(constants.SUMMARY, 'summary_file', summary_path)
                else:
                    msg = "Mini-Djerba summary not supported for assay '{0}'".format(assay)
                    self.logger.error(msg)
                    raise MiniDjerbaScriptError(msg)
            # core params (eg. the CGI author name) are unchanged from the input JSON
            config.add_section(cc.CORE)
            core_params = data[cc.CONFIG][cc.CORE]
            for k in core_params.keys():
                config.set(cc.CORE, k, core_params[k])
            # run configure_from_parser() to fill in defaults, and extract updated data
            new_data = self.base_extract(self.configure_from_parser(config))
            data = self.update_report_data(new_data, data, force)
            out_name = "{0}.updated.json".format(data[cc.CORE][cc.REPORT_ID])
            out_path = os.path.join(out_dir, out_name)
            with open(out_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
                out_file.write(json.dumps(data))
            self.logger.debug('Wrote updated JSON data to {0}'.format(out_path))
        else:
            self.logger.debug('No additional config given, rendering existing JSON')
        self.render_from_cache(data, doc_key, out_dir, pdf)
        self.logger.info('Mini-Djerba report mode complete')

    def setup(self, out_dir, json_path):
        """
        Read an existing JSON file (if any), write INI and summary files ready for editing
        INI contains placeholder values for PHI; summary file contains text from the JSON
        All patient info results keys appear in INI; use a subset for supplementary
        """
        write_summary = True
        if json_path:
            with open(json_path, encoding=cc.TEXT_ENCODING) as in_file:
                data = json.loads(in_file.read())
            patient_info = data[cc.PLUGINS][self.PATIENT_INFO][cc.RESULTS]
            supplement = data[cc.PLUGINS][self.SUPPLEMENT][cc.RESULTS]
            self.logger.debug("Supplement: {0}".format(supplement))
            if self.has_summary(data):
                text_key = summary_plugin.SUMMARY_TEXT
                text = data[cc.PLUGINS][self.SUMMARY][cc.RESULTS][text_key]
            else:
                # existing JSON without a summary plugin (eg. PWGS); do not write summary
                write_summary = False
        else:
            patient_info = patient_info_plugin.PATIENT_DEFAULTS
            text = self.SUMMARY_DEFAULT
            supplement = {
                supplement_plugin.REPORT_SIGNOFF_DATE: strftime('%Y/%m/%d'),
                supplement_plugin.GENETICIST: supplement_plugin.GENETICIST_DEFAULT,
                supplement_plugin.GENETICIST_ID: supplement_plugin.GENETICIST_ID_DEFAULT
            }
        # write the text output, if required
        if write_summary:
            summary_path = os.path.join(out_dir, self.SUMMARY_FILENAME)
            with open(summary_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
                out_file.write(text)
                self.logger.debug('Wrote summary to '+summary_path)
        else:
            self.logger.debug('No summary text in input JSON; omitting summary file')
        # write the INI output; patient_info and supplementary sections only
        config = ConfigParser()
        config.add_section(self.PATIENT_INFO)
        for key, value in patient_info.items():
            config.set(self.PATIENT_INFO, key, value)
        config.add_section(self.SUPPLEMENT)
        for key in self.SUPPLEMENT_KEYS:
            config.set(self.SUPPLEMENT, key, supplement[key])
        ini_path = os.path.join(out_dir, self.INI_FILENAME) 
        with open(ini_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
            config.write(out_file)
        self.logger.debug('Wrote INI to '+ini_path)
        self.logger.info('Mini-Djerba setup mode complete')

    def validate_ini(self, ini_path):
        """
        Validate contents of the mini-Djerba INI file
        Existence/readability already checked
        Must have *exactly* 2 sections: patient_info and supplement.body
        Each section must have *exactly* the user-adjustable params
        (core and summary are added later)
        """
        config = ConfigParser()
        config.read(ini_path)
        sections = config.sections()
        if not (len(sections)==2 and \
                self.PATIENT_INFO in sections and \
                self.SUPPLEMENT in sections):
            expected = [self.PATIENT_INFO, self.SUPPLEMENT]
            msg = "Bad INI sections; expected {0}, found {1}".format(expected, sections)
            self.logger.error(msg)
            raise MiniDjerbaScriptError(msg)
        self.validate_patient_info(dict(config.items(self.PATIENT_INFO)))
        self.validate_supplementary(dict(config.items(self.SUPPLEMENT)))

    def validate_patient_info(self, patient_info):
        found = set(patient_info.keys())
        expected = set(patient_info_plugin.PATIENT_DEFAULTS.keys())
        if not found == expected:
            msg = "Bad patient info fields; expected {0}, found {1}".format(expected, found)
            self.logger.error(msg)
            raise MiniDjerbaScriptError(msg)
        dob = patient_info[patient_info_plugin.PATIENT_DOB]
        if not is_valid_date(dob):
            msg = "Patient DOB {0} is not in YYYY-MM-DD format".format(dob)
            self.logger.error(msg)
            raise MiniDjerbaScriptError(msg)

    def validate_supplementary(self, supplementary):
        found = set(supplementary.keys())
        expected = set(self.SUPPLEMENT_KEYS)
        if not found == expected:
            msg = "Bad supplementary fields; expected {0}, found {1}".format(expected, found)
            self.logger.error(msg)
            raise MiniDjerbaScriptError(msg)
        signoff_date = supplementary[supplement_plugin.REPORT_SIGNOFF_DATE]
        if not is_valid_date(signoff_date):
            msg = "Report signoff date {0} is not in YYYY-MM-DD format".format(signoff_date)
            self.logger.error(msg)
            raise MiniDjerbaScriptError(msg)


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
            v.validate_output_dir(args.out_dir)
        elif args.subparser_name == constants.REPORT:
            for in_path in [args.json, args.ini, args.summary]:
                if in_path != None:
                    v.validate_input_file(in_path)
            for dir_path in [args.out_dir, args.work_dir]:
                if dir_path != None:
                    v.validate_output_dir(dir_path)
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

    def get_ini_path(self):
        return self._get_arg('ini')

    def get_json_path(self):
        return self._get_arg('json')

    def get_out_dir(self):
        return self._get_arg('out_dir')

    def get_summary_path(self):
        return self._get_arg('summary')


class MiniDjerbaScriptError(Exception):
    pass

