"""List inputs to a Djerba clinical report"""

import json
import sys
from configparser import ConfigParser
from djerba.configure import provenance_reader
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
        self.out_path = args.output
        self.wgs_only = args.wgs_only
        if self.wgs_only and self.ini_path:
            msg = "INI path for Mavis results not required in WGS-only mode"
            self.logger.error(msg)
            raise RuntimeError(msg)
        v = path_validator(self.log_level, self.log_path)
        if self.ini_path:
            v.validate_input_file(self.ini_path)
        if self.out_path:
            v.validate_output_file(self.out_path)
        self.logger.info("Preparing file provenance reader for study {0}, donor {1}".format(args.study, args.donor))
        self.provenance_reader = provenance_reader(args.provenance, args.study, args.donor, self.log_level, self.log_path)
        self.logger.info("File provenance reader is ready")

    def read_ini_mavis(self):
        self.logger.info("Reading Mavis input from '{0}'".format(self.ini_path))
        cp = ConfigParser()
        with open(self.ini_path) as in_file:
            try:
                cp.read_file(in_file)
            except Exception as err:
                msg = "Error loading INI from path '{0}'; ".format(self.ini_path)+\
                      "check input is in valid INI format: {0}".format(err)
                self.logger.error(msg)
                raise
        if not cp.has_option(ini.DISCOVERED, ini.MAVIS_FILE):
            msg = "Cannot find Mavis input in '{0}'; ".format(self.ini_path)+\
                  "check if input is a complete and valid Djerba INI"
            self.logger.error(msg)
            raise RuntimeError(msg)
        mavis_path = cp.get(ini.DISCOVERED, ini.MAVIS_FILE)
        self.logger.info("Found Mavis input: '{0}'".format(mavis_path))
        return ['mavis', mavis_path]

    def read_provenance_inputs(self):
        """Read input descriptions/paths from file provenance"""
        paths = []
        self.logger.info("Reading WG inputs from file provenance")
        paths.append(['variantEffectPredictor', self.provenance_reader.parse_maf_path()])
        paths.append(['sequenza', self.provenance_reader.parse_sequenza_path()])
        paths.append(['WG_tumour_bam', self.provenance_reader.parse_wg_bam_path()])
        paths.append(['WG_tumour_bam-index', self.provenance_reader.parse_wg_index_path()])
        paths.append(['WG_reference_bam', self.provenance_reader.parse_wg_bam_ref_path()])
        paths.append(['WG_reference_bam-index', self.provenance_reader.parse_wg_index_ref_path()])
        if self.wgs_only:
            self.logger.info("WG-only mode; omitting WT inputs from file provenance")
        else:
            self.logger.info("Reading WT inputs from file provenance")
            paths.append(['rsem', self.provenance_reader.parse_gep_path()])
            paths.append(['WT_bam', self.provenance_reader.parse_wt_bam_path()])
            paths.append(['WT_bam-index', self.provenance_reader.parse_wt_index_path()])
            paths.append(['starfusion', self.provenance_reader.parse_starfusion_predictions_path()])
            paths.append(['delly', self.provenance_reader.parse_delly_path()])
            paths.append(['arriba', self.provenance_reader.parse_arriba_path()])
        self.logger.info("Finished getting inputs from file provenance")
        return paths

    def run(self):
        """Mavis results path from config.ini, everything else from file provenance"""
        paths = []
        if self.ini_path:
            self.logger.info("Reading Mavis input")
            paths.append(self.read_ini_mavis())
        else:
            self.logger.info("INI path not supplied, omitting Mavis input")
        paths.extend(self.read_provenance_inputs())
        self.logger.info("Inputs read; writing output")
        if self.out_path:
            with open(self.out_path, 'w') as out_file:
                for pair in paths:
                    print("\t".join([str(x) for x in pair]), file=out_file)
            self.logger.info("Finished; output written to {0}".format(self.out_path))
        else:
            for pair in paths:
                print("\t".join([str(x) for x in pair]), file=sys.stdout)
            self.logger.info("Finished; output written to STDOUT")
