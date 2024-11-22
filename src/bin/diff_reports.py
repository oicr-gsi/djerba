#! /usr/bin/env python3

"""Diff two Djerba JSON reports"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory

from djerba.util.benchmark_tools import report_equivalence_tester
from djerba.util.logger import logger
from djerba.util.validator import path_validator

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Compare two JSON reports output by Djerba. Exit status is 0 if reports are equivalent, 1 otherwise. Run with --verbose for a summary and/or --print to view the full diff.',
        epilog='Run with -h/--help for additional information',
    )
    parser.add_argument('-r', '--report', metavar='PATH', help='Path to Djerba JSON report file. Must be supplied exactly twice.', required=True, action='append')
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-l', '--log-path', metavar='PATH', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('-p', '--print', action='store_true', help='Print a full diff to STDOUT; prints "NONE" if reports are identical')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode; logging errors only')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    return parser

def main(args):
    reports = args.report
    if len(reports)!=2:
        print("ERROR: Must have exactly 2 JSON report files, each specified wtih -r/--report", file=sys.stderr)
        sys.exit(1)
    log_level = logger.get_log_level(args.debug, args.verbose, args.quiet)
    if args.log_path:
        path_validator(log_level).validate_output_file(args.log_path)
    validator = path_validator(log_level, args.log_path)
    for report in reports:
        validator.validate_input_file(report)
    delta_path = None # TODO make configurable
    tester = report_equivalence_tester(reports, delta_path, log_level, args.log_path)
    if args.print:
        print(tester.get_diff_text())
    if tester.is_equivalent():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
