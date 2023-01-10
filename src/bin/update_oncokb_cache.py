#! /usr/bin/env python3

"""Update the OncoKB cache"""

import argparse
import sys
from argparse import RawTextHelpFormatter

sys.path.pop(0) # do not import from script directory

from djerba.extract.oncokb.cache import oncokb_cache
from djerba.util.logger import logger
from djerba.util.validator import path_validator

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Update Djerba\'s JSON cache files for OncoKB data.\n- This script is for convenience/demonstration purposes; for production use, see the --update-cache and --apply-cache options to djerba.py.\n- This script is *not* aware of the OncoTree code, and simply writes to the given cache directory.',
        epilog='Run with -h/--help for additional information',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-c', '--cache-dir', metavar='PATH', help='Directory for output of JSON cache files; should *include* the OncoTree subdirectory, if any', required=True)
    parser.add_argument('-i', '--input-dir', metavar='PATH', help='Djerba report directory; must be created with --no-cleanup', required=True)
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-l', '--log-path', metavar='PATH', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode; logging errors only')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    return parser

def main(args):
    log_level = logger.get_log_level(args.debug, args.verbose, args.quiet)
    validator = path_validator(log_level)
    if args.log_path:
        validator.validate_output_file(args.log_path)
    validator.validate_input_dir(args.input_dir)
    validator.validate_output_dir(args.cache_dir)
    cache = oncokb_cache(args.cache_dir, log_level=log_level, log_path=args.log_path)
    cache.update_cache_files(args.input_dir)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
