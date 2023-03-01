#! /usr/bin/env python3

"""merge two pdfs"""

import argparse
import sys
import traceback

sys.path.pop(0) # do not import from script directory

from djerba.util.logger import logger
from djerba.render.render import pdf_renderer
from djerba.util.validator import path_validator

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Merge two PDFs, eg. clinical and research reports.'
    )

    parser.add_argument('pdf1', metavar='PDF_PATH_1', help='pdf to appear first in merged pdf')
    parser.add_argument('pdf2', metavar='PDF_PATH_2', help='pdf to appear second in merged pdf')
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-l', '--log-path', metavar='PATH', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('-o', '--output', metavar='PATH', help='PDF output file path', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    return parser

def main(args):
    log_level = logger.get_args_log_level(args)
    val = path_validator(log_level, args.log_path)
    val.validate_input_file(args.pdf1)
    val.validate_input_file(args.pdf2)
    val.validate_output_file(args.output)
    # static method; no object creation needed
    log = logger().get_logger(log_level, 'pdf_merger', args.log_path)
    try:
        pdf_renderer.merge_pdfs(args.pdf1, args.pdf2, args.output)
    except Exception as err:
        msg = "Unexpected error of type {0} in PDF rendering: {1}".format(type(err).__name__, err)
        log.error(msg)
        trace = ''.join(traceback.format_tb(err.__traceback__))
        log.error('Traceback: {0}'.format(trace))
        raise
    log.info("Merged PDF inputs {0} and {1} to output {2}".format(args.pdf1, args.pdf2, args.output))


if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
