#! /usr/bin/env python3

"""merge two pdfs"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory

from djerba.util.logger import logger
from djerba.render.render import pdf_renderer
from djerba.util.validator import path_validator

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Merge clinical and research reports.'
    )
    parser.add_argument('-p1', '--pdf1', metavar='PATH', help='pdf to appear first in merged pdf', required=True)
    parser.add_argument('-p2', '--pdf2', metavar='PATH', help='pdf to appear second in merged pdf', required=True)
    parser.add_argument('-o', '--output', metavar='PATH', help='output name and location', required=True)
    parser.add_argument('-l', '--log-path', metavar='PATH', help='Output file for log messages; defaults to STDERR')
    return parser

def main(args):
    pdf_renderer().merge_pdfs(args.pdf1,args.pdf2,args.output)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
