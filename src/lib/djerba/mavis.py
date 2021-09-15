"""Class to manually run the Mavis workflow"""

import json
import logging
import os
import re
import subprocess
from configparser import ConfigParser
from subprocess import CalledProcessError
from shutil import copyfile, which

import djerba.util.constants as constants
from djerba.configure import provenance_reader
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class mavis_runner(logger):

    CROMWELL_OPTIONS = 'cromwell_options.json'
    TEMPLATE_NAME = 'mavis_config_template.json'
    INPUT_CONFIG = 'mavis_settings.ini'
    WAIT_SCRIPT_NAME = 'wait_for_mavis.py'

    # input file keys
    WT_BAM = 'wt_bam'
    WT_INDEX = 'wt_index'
    STARFUSION = 'starfusion'

    # mavis workflow config keys
    MAVIS_DONOR = 'mavis.donor'
    MAVIS_INPUT_BAMS = 'mavis.inputBAMs'
    MAVIS_BAM = 'bam'
    MAVIS_BAM_INDEX = 'bamIndex'
    MAVIS_SV_DATA = 'mavis.svData'
    MAVIS_SV_FILE = 'svFile'

    # ini file params
    CONFIG_NAME_KEY = 'config_name'
    CROMWELL_HOST_URL_KEY = 'cromwell_host_url'
    CROMWELL_SCRATCH_DIR_KEY = 'cromwell_scratch_dir'
    EMAIL_KEY = 'email'
    PROVENANCE_KEY = 'provenance'
    SETTINGS_KEY = 'settings'
    WDL_KEY = 'wdl'

    def __init__(self, args):
        self.args = args
        self.log_level = self.get_log_level(self.args.debug, self.args.verbose, self.args.quiet)
        self.log_path = self.args.log_path
        if self.log_path:
            # we are verifying the log path, so don't write output there yet
            path_validator(self.log_level).validate_output_file(self.log_path)
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.data_dir = os.path.join(os.path.dirname(__file__), constants.DATA_DIR_NAME)
        self.wait_script = which(self.WAIT_SCRIPT_NAME)
        if not self.wait_script:
            msg = "Unable to find {0} on the PATH".format(self.WAIT_SCRIPT_NAME)
            self.logger.error(msg)
            raise RuntimeError(msg)
        # validate the command-line arguments
        validator = path_validator(self.log_level, self.log_path)
        if not (args.ready or args.execute):
            msg = "Must specify at least one of --ready or --execute"
            self.logger.error(msg)
            raise ValueError(msg)
        elif args.ready:
            if not args.donor and args.study:
                msg = "--ready requires --donor and --study"
                self.logger.error(msg)
                raise ValueError(msg)
        self._read_config(args.config)
        validator.validate_output_dir(args.work_dir)
        self.work_dir = os.path.abspath(args.work_dir)
        self.dry_run = args.dry_run
        self.unit = args.unit

    def _read_config(self, config_path):
        """Set instance variables from the config file"""
        validator = path_validator(self.log_level, self.log_path)
        if config_path:
            validator.validate_input_file(config_path)
        else:
            config_path = os.path.join(self.data_dir, self.INPUT_CONFIG)
        config = ConfigParser()
        config.read(config_path)
        settings = config[self.SETTINGS_KEY]
        self.config_name = settings.get(self.CONFIG_NAME_KEY)
        self.cromwell_host_url = settings.get(self.CROMWELL_HOST_URL_KEY)
        self.cromwell_scratch_dir = settings.get(self.CROMWELL_SCRATCH_DIR_KEY)
        self.email_recipients = settings.get(self.EMAIL_KEY)
        self.provenance_path = settings.get(self.PROVENANCE_KEY)
        self.wdl_path = settings.get(self.WDL_KEY)
        for input_path in [self.provenance_path, self.wdl_path]:
            validator.validate_input_file(input_path)

    def execute(self, config):
        """Execute the Mavis workflow on a Cromwell server"""
        cromwell_options = os.path.join(self.data_dir, self.CROMWELL_OPTIONS)
        run_command = [
            'java', '-jar', os.path.join(os.environ['CROMWELL_ROOT'], 'share', 'cromwell.jar'),
            'submit', self.wdl_path,
            '--inputs', config,
            '--host', self.cromwell_host_url,
            '--options', cromwell_options
        ]
        self.logger.info("Submitting workflow to Cromwell")
        if self.dry_run:
            self.logger.info("Dry-run mode, omitting command: {0}".format(run_command))
            cromwell_job_id = 'DRY-RUN'
        else:
            result = self.run_subprocess(run_command)
            # extract cromwell job ID from output
            cromwell_job_id = None
            words = result.stdout.split()
            for i in range(len(words)):
                if words[i]=='Workflow' and words[i+2]=='submitted':
                    cromwell_job_id = words[i+1]
                    break
            if cromwell_job_id == None:
                msg = "Cannot find Cromwell job ID from STDOUT: {0}".format(result.stdout)
                self.logger.error(msg)
                raise RuntimeError(msg)
        # use cromwell job ID to launch the wait/copy script
        wait_command = [
            'qsub',
            '-P', 'gsi',
            '-l', 'h_vmem=1G',
            '-o', os.path.join(self.work_dir, 'waitlog'),
            '-e', os.path.join(self.work_dir, 'waitlog'),
            '-N', 'mavis_wait_{}'.format(self.find_analysis_unit()),
            self.wait_script,
            '--id', cromwell_job_id,
            '--source', self.cromwell_scratch_dir,
            '--dest', self.work_dir,
            '--email', self.email_recipients
        ]
        self.logger.info("Submitting wait job")
        if self.dry_run:
            self.logger.info("Dry-run mode, omitting command: {0}".format(wait_command))
        else:
            result = self.run_subprocess(wait_command)

    def find_analysis_unit(self):
        """Find the applicable analysis unit string"""
        if self.unit:
            self.logger.info("Using user-supplied analysis unit: {0}".format(self.unit))
            unit = self.unit
        else:
            self.logger.info("Finding analysis unit string from file provenance")
            reader = provenance_reader(self.provenance_path, self.args.study, self.args.donor, self.log_level, self.log_path)
            unit = reader.find_analysis_unit()
            if unit == None:
                self.logger.warning("Cannot find analysis unit, using 'UNKNOWN' as placeholder")
                unit = 'UNKNOWN'
            else:
                self.logger.info("Found analysis unit: {0}".format(unit))
            self.unit = unit
        return unit

    def find_inputs(self):
        """Find Mavis inputs from file provenance"""
        reader = provenance_reader(self.provenance_path, self.args.study, self.args.donor, self.log_level, self.log_path)
        inputs = {
            self.WT_BAM: reader.parse_wt_bam_path(), # STAR
            self.WT_INDEX: reader.parse_wt_index_path(), # STAR
            self.STARFUSION: reader.parse_starfusion_predictions_path(), # starFusion
        }
        return inputs
        self.logger.info("Mavis launch done")

    def link_and_copy_inputs(self, inputs):
        """Link/copy inputs to the working directory"""
        local = {}
        for key in [self.WT_BAM, self.WT_INDEX]:
            dest = os.path.join(self.work_dir, os.path.basename(inputs[key]))
            try:
                os.symlink(inputs[key], dest)
            except FileExistsError as err:
                self.logger.warning("Not making link: {0}".format(err))
            local[key] = dest
        starfusion_dest = os.path.join(self.work_dir, os.path.basename(inputs[self.STARFUSION]))
        copyfile(inputs[self.STARFUSION], starfusion_dest)
        local[self.STARFUSION] = starfusion_dest
        return local

    def main(self):
        """Main method to run Mavis operations"""
        action = 0 # bitwise flag to show which actions were taken
        if self.args.ready:
            self.logger.info("Finding inputs in file provenance: "+self.provenance_path)
            inputs = self.find_inputs()
            self.logger.info("Linking/copying inputs to working directory: "+self.work_dir)
            local_inputs = self.link_and_copy_inputs(inputs)
            self.logger.info("Writing JSON Cromwell config")
            config_json = self.write_config(local_inputs)
            action += 1
        else:
            config_json = os.path.join(self.work_dir, self.config_name)
            path_validator().validate_input_file(config_json)
        if self.args.execute:
            self.logger.info("Launching Mavis WDL: "+self.wdl_path)
            self.execute(config_json)
            action += 2
        self.logger.info("Finished.")
        return action

    def run_subprocess(self, command):
        self.logger.info("Running subprocess command: {0}".format(command))
        self.logger.debug("Command string: "+" ".join(command))
        result = subprocess.run(command, capture_output=True, encoding=constants.TEXT_ENCODING)
        self.logger.debug("STDOUT: '{0}'".format(result.stdout))
        self.logger.debug("STDERR: '{0}'".format(result.stderr))
        try:
            result.check_returncode()
        except CalledProcessError as err:
            self.logger.error("Subprocess command failed: {0}".format(err))
            raise
        self.logger.info("Subprocess command done.")
        return result

    def write_config(self, inputs):
        in_path = os.path.join(self.data_dir, self.TEMPLATE_NAME)
        with open(in_path) as in_file:
            config = json.loads(in_file.read())
        # complete the data structure and write as JSON to work_dir
        config[self.MAVIS_DONOR] = self.args.donor
        config[self.MAVIS_INPUT_BAMS][0][self.MAVIS_BAM] = inputs[self.WT_BAM]
        config[self.MAVIS_INPUT_BAMS][0][self.MAVIS_BAM_INDEX] = inputs[self.WT_INDEX]
        config[self.MAVIS_SV_DATA][0][self.MAVIS_SV_FILE] = inputs[self.STARFUSION]
        out_path = os.path.join(self.work_dir, self.config_name)
        with open(out_path, 'w') as out_file:
            out_file.write(json.dumps(config, indent=4, sort_keys=True))
        return out_path
