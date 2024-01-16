#! /usr/bin/env python3

"""
Script to run a reduced set of Djerba operations: In particular, updating patient info and summary text
"""

import sys
sys.path.pop(0) # do not import from script directory

import argparse
from tempfile import TemporaryDirectory
import djerba.util.mini.constants as constants
from djerba.util.mini.main import main, arg_processor, MiniDjerbaScriptError
from djerba.util.mini.mdc import MDCFormatError

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
	description='Mini-Djerba: A tool for updating bioinformatics clinical reports',
	epilog='Run any subcommand with -h/--help for additional information'
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-l', '--log-path', help='Output file for log messages; defaults to STDERR')
    subparsers = parser.add_subparsers(title='subcommands', help='sub-command help', dest='subparser_name')
    ready_parser = subparsers.add_parser(constants.READY, help='Ready an MDC (mini-Djerba config) file')
    ready_parser.add_argument('-j', '--json', metavar='PATH', help='Existing report JSON. Optional, if not given will generate a blank config file.')
    ready_parser.add_argument('-o', '--out', metavar='PATH', default='config.mdc', help='Output path. Optional, defaults to config.mdc in the current directory.')
    update_parser = subparsers.add_parser(constants.UPDATE, help='Update an existing JSON report file; render HTML and optional PDF')
    update_parser.add_argument('-c', '--config', metavar='PATH', required=True, help='Path to an MDC (mini-Djerba config) file')
    update_parser.add_argument('-f', '--force', action='store_true', help='Force update of mismatched plugin versions')
    update_parser.add_argument('-j', '--json', metavar='PATH', required=True, help='Path to the Djerba report JSON file to be updated')
    update_parser.add_argument('-o', '--out-dir', metavar='DIR', default='.', help='Directory for output files. Optional, defaults to the current directory.')
    update_parser.add_argument('-p', '--pdf', action='store_true', help='Generate PDF output from HTML')
    update_parser.add_argument('-u', '--write-json', action='store_true', help='Write updated JSON to the output directory')
    update_parser.add_argument('-w', '--work-dir', metavar='PATH', help='Path to workspace directory; optional, defaults to a temporary directory')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    ap = arg_processor(args)
    try:
        with TemporaryDirectory(prefix='mini_djerba_') as tmp_dir:
            main(tmp_dir, ap.get_log_level(), ap.get_log_path()).run(args)
    except MDCFormatError as err:
        msg = "Configuration error: Please check the -c/--config file and try again."
        print(msg, file=sys.stderr)
        raise
    except Exception as err:
        msg = "Unexpected Mini-Djerba error! Contact the developers."
        raise MiniDjerbaScriptError(msg) from err
