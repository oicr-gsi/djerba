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
    # TODO output from setup should include a blank INI file, with parameters for a set of plugins (exactly which ones TBD)
    setup_parser.add_argument('-b', '--base', metavar='DIR', required=True, help='base directory in which to create the working directory')
    setup_parser.add_argument('-n', '--name', metavar='NAME', required=True, help='name for working directory; typically the patient identifier')
    config_parser = subparsers.add_parser(constants.CONFIGURE, help='get configuration parameters')
    config_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    config_parser.add_argument('-o', '--out', metavar='PATH', required=True, help='Path for output of fully specified INI config file')
    config_parser.add_argument('-w', '--work-dir', metavar='PATH', required=True, help='Path to plugin workspace directory')
    # TODO want to read custom genomic summary, insert it into the JSON for archive to DB, and write the updated JSON to a local file
    # Should this be done in 'extract' mode? and move archiving to extract step? ie. report is completed by 'extract', so why not archive it at the same time?
    # Special 'update' operation to run the genomic-summary plugin *only* for greater speed, update JSON and archive to the DB -- could be part of 'render'
    # then, add --json-out and --summary arguments to 'render'
    # similar funcationality in 'all' and 'draft' modes
    extract_parser = subparsers.add_parser(constants.EXTRACT, help='extract metrics from configuration')
    extract_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with fully specified inputs')
    extract_parser.add_argument('-j', '--json', metavar='PATH', help='Path for JSON output; defaults to djerba_report.json in the plugin workspace')
    extract_parser.add_argument('-w', '--work-dir', metavar='PATH', required=True, help='Path to plugin workspace directory')
    extract_parser.add_argument('--no-cleanup', action='store_true', help='Do not clean up temporary report files')
    extract_cache_group = extract_parser.add_mutually_exclusive_group()
    extract_cache_group.add_argument('--apply-cache', action='store_true', help='Apply the offline oncoKB cache to do annotation; no contact with external oncoKB server')
    extract_cache_group.add_argument('--update-cache', action='store_true', help='Use annotation results from external oncoKB server to update the offline cache')
    render_parser = subparsers.add_parser(constants.HTML, help='read metrics directory and write HTML')
    render_parser.add_argument('-j', '--json', metavar='PATH', required=True, help='Path for JSON input')
    render_parser.add_argument('-H', '--html', metavar='PATH', help='Path for HTML output')
    render_parser.add_argument('-P', '--pdf', metavar='PATH', help='Path for PDF output; optional')
    render_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    publish_parser = subparsers.add_parser(constants.PDF, help='read Djerba HTML output and write PDF')
    publish_parser.add_argument('-H', '--html', metavar='PATH', required=True, help='Path for HTML input')
    publish_parser.add_argument('-P', '--pdf', metavar='PATH', required=True, help='Path for PDF output')
    report_parser = subparsers.add_parser(constants.REPORT, help='run configure/extract/html steps; output HTML; optionally output PDF')
    report_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    report_parser.add_argument('-j', '--json', metavar='PATH', help='Path for JSON output; defaults to djerba_report.json in the plugin workspace')
    report_parser.add_argument('-o', '--ini-out', metavar='PATH', help='Path for output of fully specified INI config file')
    report_parser.add_argument('-w', '--work-dir', metavar='PATH', required=True, help='Path to plugin workspace directory')
    report_parser.add_argument('-H', '--html', metavar='PATH', help='Path for HTML output; optional, defaults to auto-generated filename in plugin workspace')
    report_parser.add_argument('-P', '--pdf', metavar='PATH', help='Path for PDF output; optional, if not supplied, no PDF is generated')
    report_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    report_parser.add_argument('--no-cleanup', action='store_true', help='Do not clean up temporary report files')
    report_cache_group = report_parser.add_mutually_exclusive_group()
    report_cache_group.add_argument('--apply-cache', action='store_true', help='Apply the offline oncoKB cache to do annotation; no contact with external oncoKB server')
    report_cache_group.add_argument('--update-cache', action='store_true', help='Use annotation results from external oncoKB server to update the offline cache')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    ap = arg_processor(args)
    main(ap.get_work_dir(), ap.get_log_level(), ap.get_log_path()).run(args)
