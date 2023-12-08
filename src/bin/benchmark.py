#! /usr/bin/env python3

"""Generate reports for the GSICAPBENCH dataset"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory
from djerba.util.benchmark import benchmarker

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
    compare_parser = subparsers.add_parser(benchmarker.COMPARE, help='Compare two sets of Djerba benchmark reports')
    compare_parser.add_argument('-D', '--delta', metavar='PATH', type=float, help='Path to JSON file with delta values by metric; overrides default values')
    compare_parser.add_argument('-r', '--report', metavar='PATH', action='append', required=True, help='Path to a Djerba JSON report file; must be supplied twice')
    report_parser = subparsers.add_parser(benchmarker.GENERATE, help='Set up and (optionally) generate Djerba reports')
    report_parser.add_argument('-i', '--input-dir', metavar='DIR', required=True, help='Directory to scan for workflow outputs, eg. ./GSICAPBENCHyymmdd/seqware-results/')
    report_parser.add_argument('-o', '--output-dir', metavar='DIR', required=True, help='Directory in which to generate reports')
    report_parser.add_argument('--dry-run', action='store_true', help='Set up output directories and write config files, but do not generate reports')
    cache_group = report_parser.add_mutually_exclusive_group()
    cache_group.add_argument('--apply-cache', action='store_true', help='Apply the offline oncoKB cache to do annotation; no contact with external oncoKB server')
    cache_group.add_argument('--update-cache', action='store_true', help='Use annotation results from external oncoKB server to update the offline cache')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    ok = benchmarker(parser.parse_args()).run()
    if not ok:
        sys.exit(1)

