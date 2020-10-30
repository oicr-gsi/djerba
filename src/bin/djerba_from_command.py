#! /usr/bin/env python3

"""
Generate Elba config from command-line arguments

Simpler alternative to constructing a Djerba JSON config file by hand
"""

import argparse
import json
import logging
import os
import sys

sys.path.pop(0) # do not import from script directory
from djerba.report import report
from djerba.config import builder

def get_parser():
    """Construct the parser for command-line arguments"""

    parser = argparse.ArgumentParser(
        description='djerba_from_command: Generate Elba config from command-line arguments'
    )
    # General-purpose inputs
    general = parser.add_argument_group("general", "General-purpose parameters")
    general.add_argument('--conf', metavar='PATH', help="Write intermediate Djerba config to PATH in JSON format. Allows Djerba config to be inspected or saved for later use; not required to write Elba config.")
    general.add_argument('--debug', action='store_true', help="Highly verbose logging")
    general.add_argument('--force', action='store_true', help="Overwrite existing output, if any")
    general.add_argument('--log-path', metavar='PATH', help='Path of file where '+\
                        'log output will be appended. Optional, defaults to STDERR.')
    general.add_argument(
        '--out',
        metavar='PATH',
        help="Output location for Elba config. File path or - for STDOUT",
        required=True
    )
    parser.add_argument(
        '--elba-schema',
        metavar='PATH',
        help="Path to JSON schema for Elba output. Optional; relevant only in elba mode."
    )
    general.add_argument('--sample-id', metavar='ID', help='Sample ID', required=True)
    general.add_argument('--strict', action='store_true', help="Strict output checking")
    general.add_argument('--verbose', action='store_true', help="Moderately verbose logging")
    # CUSTOM_ANNOTATION
    custom = parser.add_argument_group("custom", "Parameters for CUSTOM_ANNOTATION genetic alteration")
    custom.add_argument(
        '--custom-dir',
        metavar='PATH',
        help='Directory for custom annotation input',
        required=True
    )
    custom.add_argument(
        '--gene-tsv',
        metavar='NAME',
        help="Name of TSV file with custom gene annotation",
        required=True
    )
    custom.add_argument(
        '--sample-tsv',
        metavar='NAME',
        help="Name of TSV file with custom sample annotation",
        required=True
    )
    # MUTATION_EXTENDED arguments
    mutex = parser.add_argument_group("mutex", "Parameters for MUTATION_EXTENDED genetic alteration")
    mutex.add_argument('--maf', metavar='PATH', help="MAF data file", required=True)
    mutex.add_argument('--bed', metavar='PATH', help="BED reference file", required=True)
    mutex.add_argument('--cancer-type', metavar='TYPE', help="Cancer type string", required=True)
    mutex.add_argument('--oncokb-token', metavar='TOKEN', help="OncoKB token", required=False)
    mutex.add_argument('--tcga', metavar='PATH', help="TCGA reference file", required=True)
    mutex.add_argument('--vcf', metavar='PATH', help="Filter VCF file", required=True)
    return parser

def validate_paths(args):
    """Check that input/output paths are valid"""
    input_paths = [
        args.elba_schema,
        args.maf,
        args.bed,
        args.tcga,
        args.vcf,
        os.path.join(args.custom_dir, args.gene_tsv),
        os.path.join(args.custom_dir, args.sample_tsv)
    ]
    for i in range(len(input_paths)):
        input_path = input_paths[i]
        if i==0 and input_path==None:
            continue # elba_schema is optional
        elif not os.path.exists(input_path):
            raise OSError("Input path %s does not exist" % input_path)
        if not os.path.isfile(input_path):
            raise OSError("Input path %s is not a regular file or symlink" % input_path)
        elif not os.access(input_path, os.R_OK):
            raise OSError("Input path %s is not readable" % input_path)
    output_paths = [args.out, args.conf, args.log_path]
    for i in range(len(output_paths)):
        out_path = output_paths[i]
        if i > 0 and out_path == None:
            continue # conf and log_path are optional
        elif i == 0 and out_path == '-':
            continue # out may be - for STDOUT
        out_dir = os.path.realpath(os.path.dirname(out_path))
        if os.path.isdir(out_path):
            raise OSError("Path %s is a directory; a file is required" % out_path)
        elif not os.path.exists(out_dir):
            raise OSError("Parent directory of path '%s' does not exist" % out_path)
        elif not os.access(out_dir, os.W_OK):
            raise OSError("Parent directory of path '%s' is not writable" % out_path)

def main(args):
    """Main method to run script"""
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.ERROR
    validate_paths(args)
    djerba_config_builder = builder(args.sample_id, log_level, args.log_path)
    djerba_config = djerba_config_builder.build(
        args.custom_dir,
        args.gene_tsv,
        args.sample_tsv,
        args.maf,
        args.bed,
        args.cancer_type,
        args.oncokb_token,
        args.tcga,
        args.vcf
    )
    if args.conf:
        with open(args.conf, 'w') as out:
            out.write(json.dumps(djerba_config, indent=4, sort_keys=True))
    elba_report = report(djerba_config, args.sample_id, args.elba_schema, log_level, args.log_path)
    elba_report.write_report_config(args.out, args.force, args.strict)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
