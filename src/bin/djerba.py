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
    setup_parser.add_argument('-w', '--wgs-only', action='store_true', help='setup for a WGS-only report')
    config_parser = subparsers.add_parser(constants.CONFIGURE, help='get configuration parameters')
    config_parser.add_argument('-f', '--failed', action='store_true', help='Produce report for a failed sample')
    config_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    config_parser.add_argument('-o', '--out', metavar='PATH', required=True, help='Path for output of fully specified INI config file')
    config_parser.add_argument('-w', '--wgs-only', action='store_true', help='Configure a WGS-only report')
    extract_parser = subparsers.add_parser(constants.EXTRACT, help='extract metrics from configuration')
    extract_parser.add_argument('-f', '--failed', action='store_true', help='Produce report for a failed sample')
    extract_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with fully specified inputs')
    extract_parser.add_argument('-D', '--dir', metavar='DIR', required=True, help='Directory for output of metrics')
    extract_parser.add_argument('-t', '--target-coverage', metavar='COVER', type=int, choices=[40, 80], default=40, help='Target coverage depth for report footer')
    extract_parser.add_argument('-w', '--wgs-only', action='store_true', help='Extract metrics for a WGS-only report')
    render_parser = subparsers.add_parser(constants.HTML, help='read metrics directory and write HTML')
    render_parser.add_argument('-a', '--author', metavar='NAME', help='Name of CGI author for report footer; optional')
    render_parser.add_argument('-f', '--failed', action='store_true', help='Produce report for a failed sample')
    render_parser.add_argument('-D', '--dir', metavar='DIR', help='Directory for input/output; not required if --html and --json are specified')
    render_parser.add_argument('-H', '--html', metavar='PATH', help='Path for HTML output; optional, defaults to ${PATIENT_STUDY_ID}.html in the input directory')
    render_parser.add_argument('-j', '--json', metavar='PATH', help='Path for JSON input; optional, defaults to machine-readable file in the input directory')
    render_parser.add_argument('--pdf', action='store_true', help='Write PDF to the input directory')
    render_parser.add_argument('-w', '--wgs-only', action='store_true', help='Produce a WGS-only report')
    render_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    publish_parser = subparsers.add_parser(constants.PDF, help='read Djerba HTML output and write PDF')
    publish_parser.add_argument('-H', '--html', metavar='PATH', help='Path for HTML input; optional')
    publish_parser.add_argument('-D', '--dir', metavar='DIR', required=True, help='Directory for PDF output, and for default source of HTML and patient study ID')
    draft_parser = subparsers.add_parser(constants.DRAFT, help='run configure/extract/html steps; output HTML')
    draft_parser.add_argument('-a', '--author', metavar='NAME', help='Name of CGI author for report footer; optional')
    draft_parser.add_argument('-f', '--failed', action='store_true', help='Produce report for a failed sample')
    draft_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    draft_parser.add_argument('-o', '--ini-out', metavar='PATH', help='Path for output of fully specified INI config file')
    draft_parser.add_argument('-D', '--dir', metavar='DIR', required=True, help='Directory for output of metrics')
    draft_parser.add_argument('-H', '--html', metavar='PATH', help='Path for HTML output; optional, defaults to ${PATIENT_STUDY_ID}.html in the input directory')
    draft_parser.add_argument('-t', '--target-coverage', metavar='COVER', type=int, choices=[40, 80], default=40, help='Target coverage depth for report footer')
    draft_parser.add_argument('-w', '--wgs-only', action='store_true', help='Produce a WGS-only report')
    draft_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    all_parser = subparsers.add_parser(constants.ALL, help='run all Djerba steps and output PDF')
    all_parser.add_argument('-a', '--author', metavar='NAME', help='Name of CGI author for report footer; optional')
    all_parser.add_argument('-D', '--dir', metavar='DIR', help='Directory for output of metrics')
    all_parser.add_argument('-f', '--failed', action='store_true', help='Produce report for a failed sample')
    all_parser.add_argument('-i', '--ini', metavar='PATH', required=True, help='INI config file with user inputs')
    all_parser.add_argument('-o', '--ini-out', metavar='PATH', help='Path for output of fully specified INI config file')
    all_parser.add_argument('-H', '--html', metavar='PATH', help='Path for HTML output; optional, if not given HTML is written to a temporary directory and discarded')
    all_parser.add_argument('-t', '--target-coverage', metavar='COVER', type=int, choices=[40, 80], default=40, help='Target coverage depth for report footer')
    all_parser.add_argument('-w', '--wgs-only', action='store_true', help='Produce a WGS-only report')
    all_parser.add_argument('--no-archive', action='store_true', help='Do not archive the JSON report file')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args()).run()
