#! /usr/bin/env python3

# Find the recommended gamma parameter for Sequenza

import argparse
import logging
import os
import sys

sys.path.pop(0) # do not import from script directory
from djerba.sequenza import sequenza_reader
from djerba.util.logger import logger
from djerba.util.provenance_reader import provenance_reader, sample_name_container
from djerba.util.validator import path_validator

# script mode names
LOCATE = 'locate'
READ = 'read'

def locate_sequenza_path(args):
    path_validator().validate_input_file(args.file_provenance)
    samples = sample_name_container()
    samples.set_and_validate(args.wgn, args.wgt, args.wtt)
    log_level = logger.get_args_log_level(args)
    reader = provenance_reader(args.file_provenance, args.study, args.donor, samples, log_level)
    return reader.parse_sequenza_path()

def get_parser():
    parser = argparse.ArgumentParser(
        description='sequenza_explorer: Find Sequenza results, review purity/ploidy and apply the CGI heuristic to choose a gamma parameter'
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-l', '--log-path', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('--wgn', metavar='SAMPLE', help='Whole genome normal sample name')
    parser.add_argument('--wgt', metavar='SAMPLE', help='Whole genome tumour sample name')
    parser.add_argument('--wtt', metavar='SAMPLE', help='Whole transcriptome sample name')
    subparsers = parser.add_subparsers(title='subcommands', help='sub-command help', dest='subparser_name')
    locate_parser = subparsers.add_parser(LOCATE, help='Locate Sequenza results in file provenance')
    locate_parser.add_argument('-D', '--donor', metavar='DONOR', required=True, help='Donor ID for file provenance search')
    locate_parser.add_argument('-f', '--file-provenance', metavar='PATH', default='/scratch2/groups/gsi/production/vidarr/vidarr_files_report_latest.tsv.gz',
                               help='Path to file provenance report; defaults to latest Vidarr production report')
    locate_parser.add_argument('-S', '--study', metavar='STUDY', required=True, help='Study name for file provenance search')
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
        log_level = logger.get_args_log_level(args)
        reader = sequenza_reader(args.in_path, log_level, args.log_path)
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
