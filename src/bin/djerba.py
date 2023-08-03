#! /usr/bin/env python3

"""Main script to run Djerba and produce CGI reports"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory
from djerba.core.main import main, arg_processor
import djerba.util.constants as constants

def get_parser():
    """Construct the parser for command-line arguments"""
    # --failed and --wgs-only options are no longer relevant, get these from INI config
    parser = argparse.ArgumentParser(
        description='Djerba: A tool for making bioinformatics clinical reports',
        epilog='Run any subcommand with -h/--help for additional information'
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-l', '--log-path', help='Output file for log messages; defaults to STDERR')
    subparsers = parser.add_subparsers(title='subcommands', help='sub-command help', dest='subparser_name')
    setup_parser = subparsers.add_parser(constants.SETUP, help='set up a Djerba working directory')
    # TODO output from setup should include an INI file to be completed by the user
    # setup can have options for plugin-specific behaviour like oncokb caching and file cleanup
    # see https://jira.oicr.on.ca/browse/GCGI-831
    #setup_parser.add_argument('--no-cleanup', action='store_true', help='Do not clean up temporary report files')
    #setup_cache_group = setup_parser.add_mutually_exclusive_group()
    #setup_cache_group.add_argument('--apply-cache', action='store_true', help='Apply the offline oncoKB cache to do annotation; no contact with external oncoKB server')
    #setup_cache_group.add_argument('--update-cache', action='store_true', help='Use annotation results from external oncoKB server to update the offline cache')
    setup_parser.add_argument('-b', '--base', metavar='DIR', required=True, help='base directory in which to create the working directory')
    setup_parser.add_argument('-n', '--name', metavar='NAME', required=True, help='name for working directory; typically the patient identifier')
    config_parser = subparsers.add_parser(constants.CONFIGURE, help='get configuration parameters')
    config_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    config_parser.add_argument('-o', '--ini-out', metavar='PATH', required=True, help='Path for output of fully specified INI config file')
    config_parser.add_argument('-w', '--work-dir', metavar='PATH', required=True, help='Path to plugin workspace directory')
    extract_parser = subparsers.add_parser(constants.EXTRACT, help='extract metrics from configuration')
    extract_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with fully specified inputs')
    extract_parser.add_argument('-j', '--json', metavar='PATH', help='Path for JSON output; defaults to djerba_report.json in the plugin workspace')
    extract_parser.add_argument('-w', '--work-dir', metavar='PATH', required=True, help='Path to plugin workspace directory')
    extract_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    # TODO --summary will run a 'mini-extract' step to update the genomic summary with the given file
    # if --summary is in effect, --json-out writes updated JSON to a file, --no-archive cancels archiving
    # see https://jira.oicr.on.ca/browse/GCGI-832
    render_parser = subparsers.add_parser(constants.RENDER, help='read JSON and write HTML, with optional PDF')
    render_parser.add_argument('-j', '--json', metavar='PATH', required=True, help='Path for JSON input')
    render_parser.add_argument('-o', '--out-dir', metavar='DIR', required=True, help='Directory for output files')
    render_parser.add_argument('-p', '--pdf', action='store_true', help='Generate PDF output from HTML')
    #render_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    # revised json will be written to out_dir
    #render_parser.add_argument('-s', '--summary', metavar='PATH', help='File with updated genomic summary text')
    report_parser = subparsers.add_parser(constants.REPORT, help='run configure/extract/html steps; output HTML; optionally output PDF')
    report_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    report_parser.add_argument('-o', '--out-dir', metavar='DIR', required=True, help='Directory for output files')
    report_parser.add_argument('-w', '--work-dir', metavar='PATH', required=True, help='Path to plugin workspace directory')
    report_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    ap = arg_processor(args)
    main(ap.get_work_dir(), ap.get_log_level(), ap.get_log_path()).run(args)
