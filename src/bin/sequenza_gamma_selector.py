#! /usr/bin/env python3

# Find the recommended gamma parameter for Sequenza

import argparse
import os
import sys

sys.path.pop(0) # do not import from script directory
from djerba.simple.extract.sequenza import sequenza_extractor, MissingDataError

def get_parser():
    parser = argparse.ArgumentParser(
        description='find_sequenza_gamma: Apply the CGI heuristic to choose a gamma parameter for Sequenza. Prints the result to STDOUT.'
    )
    parser.add_argument(
        '-i', '--in', metavar='PATH', required=True, dest='inPath',
        help='Path to .ZIP archive of Sequenza results'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='Print gamma selection parameters to STDERR'
    )
    return parser

def main(args):
    if not os.path.exists(args.inPath):
        raise OSError("{0} does not exist".format(args.inPath))
    elif not os.path.isfile(args.inPath):
        raise OSError("{0} is not a file".format(args.inPath))
    elif not os.access(args.inPath, os.R_OK):
        raise OSError("{0} is not readable".format(args.inPath))
    if args.verbose:
        print(sequenza_extractor(args.inPath, sys.stderr).get_default_gamma())
    else:
        print(sequenza_extractor(args.inPath).get_default_gamma())

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
