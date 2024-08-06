#! /usr/bin/env python3

"""
Script to run a reduced set of Djerba operations: In particular, updating patient info and summary text
"""

import sys
sys.path.pop(0) # do not import from script directory

import argparse
import logging
import time
import threading
from email_validator import EmailNotValidError
from tempfile import TemporaryDirectory
import djerba.util.mini.constants as constants
from djerba.core.main import DjerbaVersionMismatchError
from djerba.util.date import DjerbaDateFormatError
from djerba.util.mini.main import main, arg_processor, MiniDjerbaScriptError
from djerba.version import get_djerba_version

class Spinner:
    # See https://stackoverflow.com/a/39504463
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while True:
            for cursor in '|/-\\': yield cursor

    def __init__(self, printable=True, delay=None):
        self.printable = printable
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): self.delay = delay

    def spinner_task(self):
        while self.busy:
            if self.printable:
                sys.stdout.write(next(self.spinner_generator))
                sys.stdout.flush()
            time.sleep(self.delay)
            if self.printable:
                sys.stdout.write('\b')
                sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        if self.printable:
            sys.stdout.write('Running mini-Djerba... ')
            sys.stdout.flush()
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        if self.printable:
            sys.stdout.write('\bfinished.\n')
            sys.stdout.flush()
        time.sleep(self.delay)
        if exception is not None:
            return False

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
	description='Mini-Djerba: A tool for updating bioinformatics clinical reports',
	epilog='For details, run any subcommand with -h/--help, or visit https://djerba.readthedocs.io/en/latest/mini_djerba.html'
    )
    parser.add_argument('-d', '--debug', action='store_true', help='More verbose logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Logging for error messages only')
    parser.add_argument('-s', '--silent', action='store_true', help='No logging or progress spinner')
    parser.add_argument('-l', '--log-path', help='Output file for log messages; defaults to STDERR')
    parser.add_argument('--version', action='store_true', help='Print the version number and exit')
    subparsers = parser.add_subparsers(title='subcommands', help='sub-command help', dest='subparser_name')
    setup_parser = subparsers.add_parser(constants.SETUP, help='Set up config files')
    setup_parser.add_argument('-j', '--json', metavar='PATH', help='Existing report JSON. Optional, if not given will generate a blank config file.')
    setup_parser.add_argument('-o', '--out-dir', metavar='PATH', default='.', help='Output path. Optional, defaults to the current working directory.')
    report_parser = subparsers.add_parser(constants.REPORT, help='Generate HTML/PDF documents from a report JSON file')
    report_parser.add_argument('-f', '--force', action='store_true', help='Force update of mismatched plugin versions')
    report_parser.add_argument('-i', '--ini', metavar='PATH', help='Path to a mini-Djerba INI config file; optional')
    report_parser.add_argument('-j', '--json', metavar='PATH', required=True, help='Path to the Djerba report JSON file to be updated')
    report_parser.add_argument('-o', '--out-dir', metavar='DIR', default='.', help='Directory for output files. Optional, defaults to the current directory.')
    report_parser.add_argument('-s', '--summary', metavar='PATH', help='Path to a summary text file; optional')
    report_parser.add_argument('-w', '--work-dir', metavar='PATH', help='Path to workspace directory; optional, defaults to a temporary directory')
    report_parser.add_argument('--no-pdf', action='store_true', help='Do not generate PDF output from HTML')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    # suppress the error stacktrace unless verbose logging is in effect
    error_message = None
    args = parser.parse_args()
    if args.version:
        print("Djerba core version {0}".format(get_djerba_version()))
        sys.exit(0)
    if args.verbose or args.debug or args.quiet:
        log_enabled = True
    else:
        log_enabled = False
    try:
        if hasattr(args, 'no_pdf'):
            args.pdf = not args.no_pdf
        ap = arg_processor(args)
        # log output or spinner, maybe neither, not both
        if args.silent:
            spin_enabled = False
            log_level = logging.CRITICAL
        elif log_enabled:
            spin_enabled = False
            log_level = ap.get_log_level()
        else:
            spin_enabled = True
            log_level = logging.CRITICAL
        with Spinner(spin_enabled):
            if hasattr(args, 'work_dir') and args.work_dir != None:
                main(args.work_dir, log_level, ap.get_log_path()).run(args)
            else:
                with TemporaryDirectory(prefix='mini_djerba_') as tmp_dir:
                    main(tmp_dir, log_level, ap.get_log_path()).run(args)
    except MiniDjerbaScriptError as err:
        error_message = "Error running Mini-Djerba: {0}".format(err)
        if log_enabled:
            raise
    except DjerbaVersionMismatchError as err:
        error_message = "Error from mismatched Djerba versions: {0}".format(err)
        if log_enabled:
            raise
    except DjerbaDateFormatError as err:
        error_message = "Incorrectly formatted date, must be the placeholder value 'YYYY-MM-DD' or a numeric date of the form 1999-12-31"
        if log_enabled:
            raise
    except OSError as err:
        error_message = "Filesystem error: {0}".format(err)
        if log_enabled:
            raise
    except EmailNotValidError as err:
        error_message = "Incorrectly formatted email address: {0}".format(err)
        if log_enabled:
            raise
    except Exception as err:
        error_message = "Unexpected Mini-Djerba error! Run 'mini_djerba --debug [mode] [options]' for details.\n"+\
            "If errors persist:\n"+\
            "- Email gsi@oicr.on.ca\n"+\
            "- Please DO NOT include personal health information (PHI)"
        if log_enabled:
            raise MiniDjerbaScriptError(error_message) from err
    if error_message:
        # only called if log_enabled is False
        print(error_message, file=sys.stderr)
        sys.exit(1)
