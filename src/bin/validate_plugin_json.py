#! /usr/bin/env python3

import argparse
import jsonschema
import logging
import os
import sys

sys.path.pop(0) # do not import from script directory
from djerba.util.logger import logger
from djerba.core.json_validator import json_validator

def get_parser():
    parser = argparse.ArgumentParser(
        description='Validate JSON output from a Djerba plugin. Input is from STDIN, eg. validate_plugin_json.py < my_plugin_data.json'
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-l', '--log-path', help='Output file for log messages; defaults to STDERR')
    return parser

def main(args):
    log_level = logger.get_args_log_level(args)
    if sys.stdin.isatty():
        sys.stderr.write('Input on STDIN must be non-empty!\n')
        parser.print_help(sys.stderr)
        sys.exit(2)
    validator = json_validator(log_level=log_level, log_path=args.log_path)
    valid = True
    try:
        validator.validate_string(sys.stdin.read())
    except jsonschema.exceptions.ValidationError:
        valid = False
    if valid:
        sys.exit(0)
    else:
        sys.exit(3)

if __name__ == '__main__':
    parser = get_parser()
    main(parser.parse_args())
