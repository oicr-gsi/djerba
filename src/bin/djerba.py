#! /usr/bin/env python3

"""Main script to run Djerba and produce CGI reports"""

import argparse
import sys

sys.path.pop(0) # do not import from script directory
from djerba.main import main
import djerba.util.constants as constants

def get_parser():
    """Construct the parser for command-line arguments"""
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
    setup_parser.add_argument('-b', '--base', metavar='DIR', required=True, help='base directory in which to create the working directory')
    setup_parser.add_argument('-n', '--name', metavar='NAME', required=True, help='name for working directory; typically the patient identifier')
    config_parser = subparsers.add_parser(constants.CONFIGURE, help='get configuration parameters')
    config_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    config_parser.add_argument('-o', '--out', metavar='PATH', required=True, help='Path for output of fully specified INI config file')
    config_parser.add_argument('--no-archive', action='store_true', help='Do not archive the fully specified INI config file')
    extract_parser = subparsers.add_parser(constants.EXTRACT, help='extract metrics from configuration')
    extract_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with fully specified inputs')
    extract_parser.add_argument('-D', '--dir', metavar='DIR', required=True, help='Directory for output of metrics')
    extract_parser.add_argument('-j', '--json', metavar='PATH', help='Output path for JSON summary')
    render_parser = subparsers.add_parser(constants.HTML, help='read metrics directory and write HTML')
    render_parser.add_argument('-D', '--dir', metavar='DIR', required=True, help='Metrics directory for input')
    render_parser.add_argument('-f', '--failed', action='store_true', help='Produce report for a failed sample')
    render_parser.add_argument('-H', '--html', metavar='PATH', required=True, help='Path for HTML output')
    render_parser.add_argument('-t', '--target-coverage', metavar='COVER', type=int, choices=[40, 80], default=40, help='Target coverage depth for report footer')
    publish_parser = subparsers.add_parser(constants.PDF, help='read Djerba HTML output and write PDF')
    publish_parser.add_argument('-H', '--html', metavar='PATH', required=True, help='Path for HTML input')
    publish_parser.add_argument('-n', '--no-footer', action='store_true', help='Omit the CGI footer text; for general-purpose HTML to PDF conversion')
    publish_parser.add_argument('-p', '--pdf', metavar='PATH', help='Path for PDF output; overrides --pdf-dir option')
    publish_parser.add_argument('-P', '--pdf-dir', metavar='DIR', help='Directory for PDF output; default filename derived from analysis unit')
    publish_parser.add_argument('-u', '--unit', metavar='UNIT', help='Analysis unit identifier; required for --pdf-dir option')
    draft_parser = subparsers.add_parser(constants.DRAFT, help='run configure/extract/html steps; output HTML')
    draft_parser.add_argument('-f', '--failed', action='store_true', help='Produce report for a failed sample')
    draft_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    draft_parser.add_argument('-o', '--ini-out', metavar='PATH', help='Path for output of fully specified INI config file')
    draft_parser.add_argument('-D', '--dir', metavar='DIR', required=True, help='Directory for output of metrics')
    draft_parser.add_argument('-j', '--json', metavar='PATH', help='Output path for JSON summary')
    draft_parser.add_argument('-H', '--html', metavar='PATH', required=True, help='Path for HTML output')
    draft_parser.add_argument('-t', '--target-coverage', metavar='COVER', type=int, choices=[40, 80], default=40, help='Target coverage depth for report footer')
    draft_parser.add_argument('--no-archive', action='store_true', help='Do not archive the fully specified INI config file')
    all_parser = subparsers.add_parser(constants.ALL, help='run all Djerba steps and output PDF')
    all_parser.add_argument('-D', '--dir', metavar='DIR', help='Directory for extracted metrics output') # uses temporary dir if not supplied
    all_parser.add_argument('-f', '--failed', action='store_true', help='Produce report for a failed sample')
    all_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    all_parser.add_argument('-o', '--ini-out', metavar='PATH', help='Path for output of fully specified INI config file')
    all_parser.add_argument('-j', '--json', metavar='PATH', help='Output path for JSON summary')
    all_parser.add_argument('-H', '--html', metavar='PATH', help='Path for HTML output') # uses temporary dir if not supplied
    all_parser.add_argument('-p', '--pdf', metavar='PATH', help='Path for PDF output; overrides --pdf-dir option')
    all_parser.add_argument('-P', '--pdf-dir', metavar='DIR', required=True, help='Directory for PDF output; default filename derived from analysis unit')
    all_parser.add_argument('-t', '--target-coverage', metavar='COVER', type=int, choices=[40, 80], default=40, help='Target coverage depth for report footer')
    all_parser.add_argument('-u', '--unit', metavar='PATH', required=True, help='Analysis unit identifier; required for --pdf-dir option')
    all_parser.add_argument('--no-archive', action='store_true', help='Do not archive the fully specified INI config file')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args()).run()
