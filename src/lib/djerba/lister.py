"""List inputs to a Djerba clinical report"""

import json
import sys
from configparser import ConfigParser
from djerba.util.logger import logger
from djerba.util.validator import path_validator
import djerba.util.ini_fields as ini

class lister(logger):

    MAVIS_SV_DATA = 'mavis.svData'
    MAVIS_SV_FILE = 'svFile'
    MAVIS_INPUT_BAMS = 'mavis.inputBAMs'
    MAVIS_BAM = 'bam'
    MAVIS_BAM_INDEX = 'bamIndex'
    
    def __init__(self, args):
        self.log_level = self.get_log_level(debug=False, verbose=args.verbose, quiet=False)
        self.log_path = args.log_path
        if self.log_path:
            # we are verifying the log path, so don't write output there yet
            path_validator(self.log_level).validate_output_file(self.log_path)
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.ini_path = args.ini
        self.mavis_path = args.mavis
        self.out_path = args.output
        self.wgs_only = args.wgs_only
        v = path_validator(self.log_level, self.log_path)
        v.validate_input_file(self.ini_path)
        if not self.wgs_only:
            v.validate_input_file(self.mavis_path)
        if self.out_path:
            v.validate_output_file(self.out_path)

    def read_discovered_param(self, config, param):
        if not config.has_option(ini.DISCOVERED, param):
            msg = "No [{0}] value in '{1}'; ".format(param, self.ini_path)+\
                  "check if input is a complete and valid Djerba INI"
            self.logger.error(msg)
            raise RuntimeError(msg)
        return config.get(ini.DISCOVERED, param)

    def read_ini_inputs(self):
        cp = ConfigParser()
        with open(self.ini_path) as in_file:
            try:
                cp.read_file(in_file)
            except Exception as err:
                msg = "Error loading INI from path '{0}'; ".format(self.ini_path)+\
                      "check input is in valid INI format: {0}".format(err)
                self.logger.error(msg)
                raise
        if not cp.has_section(ini.DISCOVERED):
            msg = "No [{0}] section in '{1}'; ".format(ini.DISCOVERED, self.ini_path)+\
                  "check if input is a complete and valid Djerba INI"
            self.logger.error(msg)
            raise RuntimeError(msg)
        paths = []
        if not self.wgs_only:
            self.logger.info("Finding GEP and MAF input")
            paths.append(self.read_discovered_param(cp, ini.GEP_FILE))
        else:
            self.logger.info("WGS-only mode, omitting GEP input")
        self.logger.info("Finding Sequenza and MAF input")
        paths.append(self.read_discovered_param(cp, ini.SEQUENZA_FILE))
        paths.append(self.read_discovered_param(cp, ini.MAF_FILE))
        return paths

    def read_mavis_inputs(self):
        # TODO should we note if inputs are WG/WT, especially for BAM files?
        # TODO do we also want the normal (reference) BAM file?
        paths = []
        with open(self.mavis_path) as in_file:
            try:
                mavis_data = json.load(in_file)
            except Exception as err:
                msg = "Error loading JSON from path '{0}'; ".format(self.mavis_path)+\
                      "check input is in valid JSON format: {0}".format(err)
                self.logger.error(msg)
                raise
        for result in mavis_data.get(self.MAVIS_SV_DATA):
            paths.append(result.get(self.MAVIS_SV_FILE))
        for result in mavis_data.get(self.MAVIS_INPUT_BAMS):
            paths.append(result.get(self.MAVIS_BAM))
            paths.append(result.get(self.MAVIS_BAM_INDEX))
        return paths

    def run(self):
        paths = []
        if self.wgs_only:
            self.logger.info("WGS-only mode, omitting Mavis inputs")
        else:
            self.logger.info("Finding Mavis inputs")
            paths.extend(self.read_mavis_inputs())
        paths.extend(self.read_ini_inputs())
        self.logger.info("Inputs read; writing output")
        if self.out_path:
            with open(self.out_path, 'w') as out_file:
                for path in paths:
                    print(path, file=out_file)
            self.logger.info("Finished; output written to {0}".format(self.out_path))
        else:
            for path in paths:
                print(path, file=sys.stdout)
            self.logger.info("Finished; output written to STDOUT")
