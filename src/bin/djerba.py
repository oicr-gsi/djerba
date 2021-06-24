#! /usr/bin/env python3

# Simplified djerba script for CGI reports only
# - supply input config
# - read inputs
# - collate results; transform from input-major to gene-major order
# - write JSON output

import argparse
import configparser
import os
import sys

sys.path.pop(0) # do not import from script directory
import djerba.ini_fields as fields
from djerba.runner import runner

#CONFIGURE = 'configure'
#EXTRACT = 'extract'
#BUILD = 'build'
#RUN_ALL = 'all'
#MODES = [CONFIGURE, EXTRACT, BUILD, RUN_ALL]
# TODO add modes for RENDER (to HTML) and PUBLISH (to PDF)
# TODO are separate modes needed?

# HOW TO RUN DJERBA:
#
# 1. CONFIGURE
# Supply an INI config file (TODO allow multiple files, eg. default settings and run params)
# Override INI arguments (if present) with command line options
# Validate the inputs; all required arguments are present
# Create the configuration, eg. by reading file provenance
# Write config JSON
#
# 2. EXTRACT
# Run singleSample.R
# Extract other params, eg. Sequenza data for given gamma
# Write files to a working directory
#
# 3. BUILD
# Collate outputs from step 2
# TODO Parse singleSample.R text outputs here, or in step 2?
# Write as a single JSON document for step 4
#
# 4. RENDER
# Use a template (Rmarkdown or Jinja) to render JSON from step 3 as HTML
#
# 5. PUBLISH
# Convert HTML from step 4 to PDF using Python


# TODO make a class to process the INI params and check consistency/completeness

# INI param types
# Settings: General system params for Djerba
# Inputs: Data to be processed
# Rscript: Inputs specifically for singleSample.R

# example settings:
# - working directory
# - JSON config path
# - logging/verbosity options
# - provenance path
# - BED interval file for TMB calculation
# - JSON config schema path (step 1)
# - JSON output schema path (step 3)

# example inputs:
# - donor
# - project
# - gamma

class djerba_validator:

    def __init__(self):
        pass

    def validate_config(self, config):
        """Validate the config params, eg. from an INI file"""
        self.validate_input_file(config[fields.SETTINGS][fields.PROVENANCE])
        self.validate_output_dir(config[fields.SETTINGS][fields.SCRATCH_DIR])
        self.validate_present(config, fields.INPUTS, fields.NORMAL_ID)
        self.validate_present(config, fields.INPUTS, fields.PATIENT_ID)
        self.validate_present(config, fields.INPUTS, fields.STUDY_ID)

    def validate_input_file(self, path):
        """Confirm an input file exists and is readable"""
        valid = False
        if not os.path.exists(path):
            raise OSError("Input path %s does not exist" % path)
        elif not os.path.isfile(path):
            raise OSError("Input path %s is not a file" % path)
        elif not os.access(path, os.R_OK):
            raise OSError("Input path %s is not readable" % path)
        else:
            valid = True
        return valid

    def validate_output_dir(self, path):
        """Confirm an output directory exists and is writable"""
        valid = False
        if not os.path.exists(path):
            raise OSError("Output path %s does not exist" % path)
        elif not os.path.isdir(path):
            raise OSError("Output path %s is not a directory" % path)
        elif not os.access(path, os.W_OK):
            raise OSError("Output path %s is not writable" % path)
        else:
            valid = True
        return valid

    def validate_present(self, config, section, param):
        # throws a KeyError if param is missing; TODO informative error message
        return config[section][param]

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Djerba: A tool for making bioinformatics clinical reports',
        epilog='Run any subcommand with --help for additional information'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Print additional status information'
    )
    subparsers = parser.add_subparsers(title='subcommands', help='sub-command help')
    config_parser = subparsers.add_parser('configure', help='get configuration parameters')
    config_parser.add_argument('-i', '--in', metavar='PATH', required=True, help='INI config file with user inputs')
    config_parser.add_argument('-o', '--out', metavar='PATH', required=True, help='Path for output of fully specified INI config file')
    extract_parser = subparsers.add_parser('extract', help='extract metrics from configuration')
    extract_parser.add_argument('-i', '--in', metavar='PATH', required=True, help='Fully specified INI config file')
    extract_parser.add_argument('-d', '--dir', metavar='DIR', required=True, help='Directory for output of metrics')
    extract_parser.add_argument('-j', '--json', metavar='PATH', help='Output path for JSON summary')
    render_parser = subparsers.add_parser('html', help='read metrics directory and write HTML')
    render_parser.add_argument('-d', '--dir', metavar='DIR', required=True, help='Metrics directory for input')
    render_parser.add_argument('-H', '--html', metavar='PATH', required=True, help='Path for HTML output')
    publish_parser = subparsers.add_parser('pdf', help='read Djerba HTML output and write PDF')
    publish_parser.add_argument('-H', '--html', metavar='PATH', required=True, help='Path for HTML input')
    publish_parser.add_argument('-p', '--pdf', metavar='PATH', required=True, help='Path for PDF output')
    all_parser = subparsers.add_parser('all', help='run all Djerba steps and output PDF')
    all_parser.add_argument('-i', '--in', metavar='PATH', required=True, help='INI config file with user inputs')
    all_parser.add_argument('-c', '--config', metavar='PATH', help='Path for output of fully specified INI config file')
    all_parser.add_argument('-d', '--dir', metavar='DIR', required=True, help='Directory for extracted metrics output') # TODO write to tempdir if not supplied?
    all_parser.add_argument('-j', '--json', metavar='PATH', help='Output path for JSON summary')
    all_parser.add_argument('-H', '--html', metavar='PATH', help='Path for HTML output')
    all_parser.add_argument('-p', '--pdf', metavar='PATH', required=True, help='Path for PDF output')
    return parser

def main(args):
    validator = djerba_validator()
    validator.validate_input_file(args.ini)
    config = configparser.ConfigParser()
    config.read(args.ini) # TODO update config with command-line options
    validator.validate_config(config)
    runner(config).run()

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
