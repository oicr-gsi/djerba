#! /usr/bin/env python3

"""Generate reports for the GSICAPBENCH dataset"""
# TODO also use this script to compare report JSON

import argparse
import sys

sys.path.pop(0) # do not import from script directory
from djerba.benchmark import benchmarker

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='benchmark: Generate reports for the GSICAPBENCH dataset',
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-i', '--input-dir', metavar='DIR', help='Directory to scan for workflow outputs, eg. ./GSICAPBENCHyymmdd/seqware-results/')
    parser.add_argument('-o', '--output-dir', metavar='DIR', help='Directory in which to generate reports')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-l', '--log-path', metavar='PATH', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('--dry-run', action='store_true', help='Set up output directories and write config files, but do not generate reports')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    benchmarker(parser.parse_args()).run()

