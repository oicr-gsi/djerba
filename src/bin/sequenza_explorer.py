#! /usr/bin/env python3

# Find the recommended gamma parameter for Sequenza

import argparse
import logging
import os
import sys

sys.path.pop(0) # do not import from script directory
from djerba.configure import provenance_reader
from djerba.sequenza import sequenza_reader
from djerba.util.validator import path_validator

# script mode names
LOCATE = 'locate'
READ = 'read'

def locate_sequenza_path(args):
    path_validator().validate_input_file(args.file_provenance)
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    reader = provenance_reader(args.file_provenance, args.project, args.donor, log_level)
    return reader.parse_sequenza_path()

def get_parser():
    parser = argparse.ArgumentParser(
        description='sequenza_explorer: Find Sequenza results, review purity/ploidy and apply the CGI heuristic to choose a gamma parameter'
    )
    subparsers = parser.add_subparsers(title='subcommands', help='sub-command help', dest='subparser_name')
    locate_parser = subparsers.add_parser(LOCATE, help='Locate Sequenza results in file provenance')
    locate_parser.add_argument('--debug', action='store_true', help='More verbose search logging')
    locate_parser.add_argument('--verbose', action='store_true', help='Verbose search logging')
    locate_parser.add_argument('-d', '--donor', metavar='DONOR', required=True, help='Donor ID for file provenance search')
    locate_parser.add_argument('-f', '--file-provenance', metavar='PATH', default='/.mounts/labs/seqprodbio/private/backups/seqware_files_report_latest.tsv.gz',
                               help='Path to file provenance report; defaults to latest production report')
    locate_parser.add_argument('-p', '--project', metavar='PROJECT', required=True, help='Project name for file provenance search')
    read_parser = subparsers.add_parser(READ, help='Read and summarize a Sequenza result .ZIP file')
    read_parser.add_argument('-i', '--in', metavar='PATH', required=True, dest='in_path', help='Path to .ZIP archive of Sequenza results')
    read_parser.add_argument('-j', '--json', metavar='PATH', help='Path for JSON output of gamma parameters and purity/ploidy')
    read_parser.add_argument('-g', '--gamma-selection', action='store_true', help='Write gamma selection parameters to STDOUT')
    read_parser.add_argument('-p', '--purity-ploidy', action='store_true', help='Write purity/ploidy table to STDOUT')
    read_parser.add_argument('-s', '--summary', action='store_true', help='Write summary with min/max purity to STDOUT')
    return parser

def main(args):
    if args.subparser_name == LOCATE:
        print(locate_sequenza_path(args))
    elif args.subparser_name == READ:
        path_validator().validate_input_file(args.in_path)
        reader = sequenza_reader(args.in_path)
        if args.gamma_selection:
            reader.print_gamma_selection()
        if args.purity_ploidy:
            reader.print_purity_ploidy_table()
        if args.summary:
            reader.print_summary()
        if args.json:
            reader.write_json(args.json)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
