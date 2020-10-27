#! /usr/bin/env python3

"""Command-line script to run Djerba functions"""

import argparse
import json
import logging
import os
import sys

sys.path.pop(0) # do not import from script directory
from djerba.report import report
from djerba.study import study
from djerba.config import validator

ELBA = 'elba'
CBIOPORTAL = 'cbioportal'
VALIDATE = 'validate'
MODES = (ELBA, CBIOPORTAL, VALIDATE)

def get_parser():
    """Construct the parser for command-line arguments"""

    epilog_str = 'Must be run in one of the following modes: '+\
                 '%s, %s, or %s. See above for additional help.' % MODES
    parser = argparse.ArgumentParser(
        description='djerba: A reporting tool for cancer bioinformatics', epilog=epilog_str)
    parser.add_argument('--config', metavar='PATH', required=True, help="Path to Djerba config file, or - to read from STDIN")
    parser.add_argument('--debug', action='store_true', help="Highly verbose logging")
    parser.add_argument('--force', action='store_true', help="Overwrite existing output, if any")
    parser.add_argument('--log-path', metavar='PATH', help='Path of file where '+\
                        'log output will be appended. Optional, defaults to STDERR.')
    parser.add_argument(
        '--out',
        metavar='PATH',
        help="Output location. For %s, may be a file or - for STDOUT; for %s, must be a directory; for %s, not required." % MODES
    )
    parser.add_argument(
        '--mode',
        metavar='MODE',
        choices=list(MODES),
        required=True,
        help="Mode of action; must be '%s', '%s' or '%s'. Respectively, these write an Elba config file; write a cBioPortal study directory; and validate a Djerba config file without writing output." % MODES
    )
    parser.add_argument(
        '--sample',
        metavar='SAMPLE_ID',
        help="Sample ID. For %s, required only if the config contains more than one sample; ignored for %s; optional for %s." % MODES
    )
    parser.add_argument('--verbose', action='store_true', help="Moderately verbose logging")

    return parser

def args_errors(args):
    """Check command-line arguments for errors"""
    errors = []
    if args.config=='-':
        pass
    elif not os.path.exists(args.config):
        errors.append("--config path '%s' does not exist" % args.config)
    elif not os.path.isfile(args.config):
        errors.append("--config path '%s' is not a file" % args.config)
    elif not os.access(args.config, os.R_OK):
        errors.append("--config path '%s' is not readable" % args.config)
    if args.log_path:
        errors.extend(output_file_errors(args.log_path, 'log'))
    if (args.mode==ELBA or args.mode==CBIOPORTAL) and args.out == None:
        errors.append("--out argument is required for %s mode" % args.mode)
    elif args.mode == ELBA:
        errors.extend(output_file_errors(args.out, 'output', True))
    elif args.mode == CBIOPORTAL:
        if not os.path.isdir(args.out):
            errors.append("--out must be a directory for %s mode" % CBIOPORTAL)
        elif not os.access(args.out, os.W_OK):
            errors.append("--out directory '%s' is not writable" % args.out)
    return errors

def output_file_errors(out_path, function, stdout_allowed=False):
    """Check if an output file path is usable"""
    errors = []
    if stdout_allowed and out_path=="-": # output to STDOUT
        pass
    else:
        out_dir = os.path.realpath(os.path.dirname(out_path))
        if os.path.isdir(out_path):
            errors.append("The %s path '%s' is a directory; a file is required" % (function, out_path))
        elif not os.path.exists(out_dir):
            errors.append("Parent of %s path '%s' does not exist" % (function, out_path))
        elif not os.path.isdir(out_dir):
            errors.append("Parent of %s path '%s' is not a directory" % (function, out_path))
        elif not os.access(out_dir, os.W_OK):
            errors.append("Parent of %s path  '%s' is not writable" % (function, out_path))
    return errors

def main(args):
    # check arguments for errors
    errors = args_errors(args)
    if len(errors)>0:
        print("Errors found in command-line arguments:", file=sys.stderr)
        for error in errors:
            print("*", error, file=sys.stderr)
        raise RuntimeError("Incorrect command-line arguments")
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.ERROR
    # read config from file path or STDIN
    if args.config=='-':
        config_file = sys.stdin
    else:
        config_file = open(args.config, 'r')
    config = json.loads(config_file.read())
    if args.config!='-':
        config_file.close()
    # run Djerba in the appropriate mode
    if args.mode == ELBA:
        validator(log_level, args.log_path).validate(config, args.sample)
        djerba_report = report(config, args.sample, log_level, args.log_path)
        djerba_report.write_report_config(args.out, args.force)
    elif args.mode == CBIOPORTAL:
        validator(log_level, args.log_path).validate(config, None, log_level)
        djerba_study = study(config, log_level, args.log_path)
        djerba_study.write_all(args.out, args.force)
    elif args.mode == VALIDATE:
        validator(log_level, args.log_path).validate(config, args.sample)
    else:
        raise ValueError("Undefined mode %s" % args.mode)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
