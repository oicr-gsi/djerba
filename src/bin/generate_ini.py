#! /usr/bin/env python3

"""Script to generate INI files for manual completion"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory

from djerba.util.logger import logger
from djerba.core.ini_generator import ini_generator
from djerba.util.validator import path_validator

def get_parser():
    parser = argparse.ArgumentParser(
        description='generate_ini.py: Generate INI files for Djerba',
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-l', '--log-path', metavar='PATH', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('-o', '--out', metavar='PATH', help='INI output file', required=True)
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('component', help='Non-core components to include', nargs='*')
    core_group = parser.add_mutually_exclusive_group()
    core_group.add_argument('-c', '--only-core', action='store_true', help='Only include core config in the INI output')
    core_group.add_argument('-n', '--no-core', action='store_true', help='Do not include core config in the INI output')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    log_level = logger.get_args_log_level(args)
    validator = path_validator(log_level)
    validator.validate_output_file(args.out)
    if args.log_path:
        validator.validate_output_file(args.log_path)
    if args.only_core:
        component_list = ['core']
    elif args.no_core:
        component_list = args.component
        if len(args.component)==0:
            raise ValueError("Cannot generate INI with an empty component list")
    else:
        component_list = ['core']
        component_list.extend(args.component)
    generator = ini_generator(log_level, args.log_path)
    generator.write_config(component_list, args.out)
