#! /usr/bin/env python3

import argparse
import sys

sys.path.pop(0) # do not import from script directory
from djerba.lister import lister

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='List the input file paths to a Djerba clinical report',
        epilog='Run with -h/--help for additional information'
    )
    parser.add_argument('-i', '--ini', metavar='PATH', help='INI file with input paths for djerba.py')
    parser.add_argument('-l', '--log-path', metavar='PATH', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('-m', '--mavis', metavar='PATH', help='JSON file with inputs for the Mavis workflow')
    parser.add_argument('-o', '--output', metavar='PATH', help='File for text output; defaults to STDOUT')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-w', '--wgs-only', action='store_true', help='WGS-only mode; process only WGS inputs')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    lister(parser.parse_args()).run()
