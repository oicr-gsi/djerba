#! /usr/bin/env python3

import argparse
import json
import sys
sys.path.pop(0) # do not import from script directory

from djerba.util.validator import path_validator
import djerba.render.constants as rc
import djerba.util.constants as constants

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='view_json.py: Print a Djerba JSON report in human-readable format',
        epilog="Djerba images are redacted by default. With --no-redact, works as a general-purpose JSON viewer."
    )
    parser.add_argument('-i', '--in', dest='in_path', metavar='PATH', required=True, help='JSON input file, or - for STDIN')
    parser.add_argument('-n', '--no-redact', action='store_true', help='Do not redact images')
    parser.add_argument('-o', '--out', metavar='PATH', required=True, help='JSON output file, or - for STDOUT')
    return parser

def main(args):
    val = path_validator()
    if args.in_path == '-':
        data = json.loads(sys.stdin.read())
    else:
        val.validate_input_file(args.in_path)
        with open(args.in_path) as in_file:
            data = json.loads(in_file.read())
    if not args.no_redact:
        for key in [rc.OICR_LOGO, rc.TMB_PLOT, rc.VAF_PLOT]:
            data[constants.REPORT][key] = 'REDACTED'
    output = json.dumps(data, sort_keys=True, indent=4)
    if args.out == '-':
        sys.stdout.write(output)
    else:
        val.validate_output_file(args.out)
        with open(args.out, 'w') as out_file:
            out_file.write(output)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
