#! /usr/bin/env python3

"""Generate reports for the GSICAPBENCH dataset"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory
import djerba.util.constants as constants
from djerba.benchmark import benchmarker

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='benchmark: Generate reports for the GSICAPBENCH dataset',
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-l', '--log-path', metavar='PATH', help='Output file for log messages; defaults to STDERR')
    subparsers = parser.add_subparsers(title='subcommands', help='sub-command help', dest='subparser_name')
    compare_parser = subparsers.add_parser(constants.COMPARE, help='Compare two sets of Djerba benchmark reports')
    compare_parser.add_argument('-a', '--all', action='store_true', dest='compare_all', help='Compare all contents of JSON files. If not given, default is to compare report elements only, not supplementary.')
    compare_parser.add_argument('-r', '--report-dir', metavar='DIR', action='append', required=True, help='Directory of reports, as generated in \'report\' mode; must be supplied twice')
    report_parser = subparsers.add_parser(constants.REPORT, help='Set up and (optionally) generate Djerba reports')
    report_parser.add_argument('-i', '--input-dir', metavar='DIR', required=True, help='Directory to scan for workflow outputs, eg. ./GSICAPBENCHyymmdd/seqware-results/')
    report_parser.add_argument('-o', '--output-dir', metavar='DIR', required=True, help='Directory in which to generate reports')
    report_parser.add_argument('--dry-run', action='store_true', help='Set up output directories and write config files, but do not generate reports')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    ok = benchmarker(parser.parse_args()).run()
    if not ok:
        sys.exit(1)

