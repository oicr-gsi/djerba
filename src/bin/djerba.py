#! /usr/bin/env python3

"""Main script to run Djerba and produce CGI reports"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory
from djerba.core.main import main, arg_processor, DjerbaInvalidNameError
from djerba.version import get_djerba_version
from djerba.util.activity import activity_tracker
import djerba.util.constants as constants

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Djerba: A tool for making bioinformatics clinical reports',
        epilog='For details, run any subcommand with -h/--help, or visit https://djerba.readthedocs.io'
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-l', '--log-path', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('--version', action='store_true', help='Print the version number and exit')
    subparsers = parser.add_subparsers(title='subcommands', help='sub-command help', dest='subparser_name')
    setup_parser = subparsers.add_parser(constants.SETUP, help='setup for a Djerba report')
    setup_parser.add_argument('-a', '--assay', metavar='NAME', required=True, help='Name of assay (case-insensitive)')
    setup_parser.add_argument('-i', '--ini', metavar='PATH', help='Output path for INI file; defaults to config.ini in current directory')
    setup_parser.add_argument('-c', '--compact', action='store_true', help="Output required manual parameters only")
    setup_parser.add_argument('-p', '--pre-populate', metavar='PATH', help='INI file with key/value pairs to pre-populate config')
    config_parser = subparsers.add_parser(constants.CONFIGURE, help='get configuration parameters')
    config_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    config_parser.add_argument('-o', '--ini-out', metavar='PATH', required=True, help='Path for output of fully specified INI config file')
    config_parser.add_argument('-w', '--work-dir', metavar='PATH', required=True, help='Path to workspace directory')
    extract_parser = subparsers.add_parser(constants.EXTRACT, help='extract metrics from configuration')
    extract_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with fully specified inputs')
    extract_parser.add_argument('-j', '--json', metavar='PATH', help='Path for JSON output; defaults to ${REPORT_ID}_report.json in the plugin workspace')
    extract_parser.add_argument('-w', '--work-dir', metavar='PATH', required=True, help='Path to workspace directory')
    extract_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    render_parser = subparsers.add_parser(constants.RENDER, help='read JSON and write HTML, with optional PDF')
    render_parser.add_argument('-j', '--json', metavar='PATH', required=True, help='Path for JSON input')
    render_parser.add_argument('-o', '--out-dir', metavar='DIR', required=True, help='Directory for output files')
    render_parser.add_argument('-p', '--pdf', action='store_true', help='Generate PDF output from HTML')
    render_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    report_parser = subparsers.add_parser(constants.REPORT, help='run configure/extract/html steps; output HTML; optionally output PDF')
    report_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    report_parser.add_argument('-o', '--out-dir', metavar='DIR', required=True, help='Directory for output files')
    report_parser.add_argument('-w', '--work-dir', metavar='PATH', help='Path to workspace directory; optional, defaults to value of --out-dir')
    report_parser.add_argument('-p', '--pdf', action='store_true', help='Generate PDF output from HTML')
    report_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    update_parser = subparsers.add_parser(constants.UPDATE, help='Update an existing JSON report file; optionally render HTML/PDF')
    group = update_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', '--ini', metavar='PATH', help='INI config file with plugins to update')
    group.add_argument('-s', '--summary', metavar='PATH', help='Text file with results summary')
    update_parser.add_argument('-f', '--force', action='store_true', help='Force update of mismatched plugin versions')
    update_parser.add_argument('-j', '--json', metavar='PATH', required=True, help='Path for JSON input')
    update_parser.add_argument('-o', '--out-dir', metavar='DIR', required=True, help='Directory for output files')
    update_parser.add_argument('-p', '--pdf', action='store_true', help='Generate PDF output from HTML')
    update_parser.add_argument('-w', '--work-dir', metavar='PATH', help='Path to workspace directory; optional, defaults to value of --out-dir')
    update_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    if args.version:
        print("Djerba core version {0}".format(get_djerba_version()))
        sys.exit(0)
    try:
        ap = arg_processor(args)
        activity_tracker(ap.get_log_level(), ap.get_log_path()).run(args)
        main(ap.get_work_dir(), ap.get_log_level(), ap.get_log_path()).run(args)
    except DjerbaInvalidNameError as err:
        print("{0}".format(err), file=sys.stderr)
        sys.exit(1)

