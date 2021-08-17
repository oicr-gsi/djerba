#! /usr/bin/env python3

# Find the recommended gamma parameter for Sequenza

import argparse
import os
import sys

sys.path.pop(0) # do not import from script directory
from djerba.extract.sequenza import sequenza_extractor

def get_parser():
    parser = argparse.ArgumentParser(
        description='sequenza_explorer: Review purity/ploidy and apply the CGI heuristic to choose a gamma parameter'
    )
    parser.add_argument(
        '-i', '--in', metavar='PATH', required=True, dest='in_path',
        help='Path to .ZIP archive of Sequenza results'
    )
    parser.add_argument(
        '-j', '--json', metavar='PATH',
        help='Path for JSON output of gamma parameters and purity/ploidy'
    )
    parser.add_argument(
        '-g', '--gamma-selection', action='store_true',
        help='Write gamma selection parameters to STDOUT'
    )
    parser.add_argument(
        '-p', '--purity-ploidy', action='store_true',
        help='Write purity/ploidy table to STDOUT'
    )
    parser.add_argument(
        '-s', '--summary', action='store_true',
        help='Write summary with min/max purity to STDOUT'
    )
    return parser

def main(args):
    if not os.path.exists(args.in_path):
        raise OSError("{0} does not exist".format(args.in_path))
    elif not os.path.isfile(args.in_path):
        raise OSError("{0} is not a file".format(args.in_path))
    elif not os.access(args.in_path, os.R_OK):
        raise OSError("{0} is not readable".format(args.in_path))
    seqex = sequenza_extractor(args.in_path)
    if args.gamma_selection:
        seqex.print_gamma_selection()
    if args.purity_ploidy:
        seqex.print_purity_ploidy_table()
    if args.summary:
        seqex.print_summary()
    if args.json:
        seqex.write_json(args.json)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
