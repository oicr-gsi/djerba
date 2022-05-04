#! /usr/bin/env python3

"""Convenience script for general-purpose HTML to PDF conversion"""

import argparse
import os
import sys

sys.path.pop(0) # do not import from script directory

from djerba.render.render import pdf_renderer
from djerba.util.validator import path_validator

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='html2pdf: Script for HTML -> PDF conversion'
    )
    parser.add_argument('-H', '--html', required=True, metavar='PATH', help="HTML input path")
    parser.add_argument('-P', '--pdf', required=True, metavar='PATH', help="PDF output path")
    return parser

def main(args):
    v = path_validator()
    v.validate_input_file(args.html)
    v.validate_output_file(args.pdf)
    pdf_renderer().run(os.path.abspath(args.html), os.path.abspath(args.pdf), footer=False)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
