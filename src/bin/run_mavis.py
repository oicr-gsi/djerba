#! /usr/bin/env python3

"""Script to manually run Mavis"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory
from djerba.mavis import mavis_runner
import djerba.util.constants as constants

def get_parser():
    """Construct the parser for command-line arguments"""
    desc = 'run_mavis: Manually run the Mavis workflow'
    epilog = 'If sample names are given, both --wgn and --wgt must be specified, with optional --wtt. Must specify at least one of --ready and --execute.'
    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    parser.add_argument('--dry-run', action='store_true', help='In execute mode, generate and log commands but do not actually run them')
    parser.add_argument('-c', '--config', metavar='FILE', help='INI config file with additional settings. Optional.')
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-D', '--donor', metavar='ID', help='Donor ID, eg. PANX_1273')
    parser.add_argument('-L', '--legacy', action='store_true', help='Run legacy CGI-Tools WDL for Mavis, instead of the current version')
    parser.add_argument('-l', '--log-path', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-r', '--ready', action='store_true', help='Ready the working directory; find, link and filter inputs, and write Crowmell config.')
    parser.add_argument('-S', '--study', metavar='ID', help='Study ID, eg. PASS01')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-w', '--work-dir', metavar='DIR', required=True, help='Working directory for input/output files')
    parser.add_argument('--wgn', metavar='SAMPLE', help='Whole genome normal sample name')
    parser.add_argument('--wgt', metavar='SAMPLE', help='Whole genome tumour sample name')
    parser.add_argument('--wtt', metavar='SAMPLE', help='Whole transcriptome sample name')
    parser.add_argument('-x', '--execute', action='store_true', help='Launch Mavis job on Cromwell server.')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    mavis_runner(parser.parse_args()).main()

