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
    general.add_argument(
        '--conf',
        metavar='PATH',
        help="Write intermediate Djerba config to PATH in JSON format. Allows Djerba config "+\
        "to be inspected or saved for later use; not required to write Elba config."
    )
    general.add_argument('--debug', action='store_true', help="Highly verbose logging")
    general.add_argument('--force', action='store_true', help="Overwrite existing output, if any")
    general.add_argument('--log-path', metavar='PATH', help='Path of file where '+\
                        'log output will be appended. Optional, defaults to STDERR.')
    general.add_argument(
        '--out',
        metavar='PATH',
        help="Output location for Elba config. File path or - for STDOUT. Optional."
    )
    general.add_argument(
        '--elba-schema',
        metavar='PATH',
        help="Path to JSON schema for Elba output. Optional."
    )
    general.add_argument(
        '--report-id',
        metavar='ID',
        help='ID string for Elba database. Optional. Only takes effect if '+\
        'an upload option is specified.'
    )
    general.add_argument('--sample-id', metavar='ID', help='Sample ID', required=True)
    general.add_argument('--strict', action='store_true', help="Strict output checking")
    general.add_argument('--verbose', action='store_true', help="Moderately verbose logging")
    # uploading modes
    upload = general.add_mutually_exclusive_group()
    upload.add_argument(
        '--upload',
        action='store_true',
        help="Upload to Elba server, with default configuration"
    )
    upload.add_argument(
        '--upload-config',
        metavar='PATH',
        help="Upload to Elba server, with custom configuration read from PATH"
    )
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

    # SEGMENTED argument
    segmented = parser.add_argument_group("seg", "Parameters for SEGMENTED genetic alteration")
    segmented.add_argument('--seg', metavar='PATH', help="SEG data file", required=True)

    return parser

def validate_paths(args):
    """Check that input/output paths are valid"""
    input_paths = [
        args.elba_schema,
        args.upload_config,
        args.maf,
        args.bed,
        args.tcga,
        args.vcf,
        os.path.join(args.custom_dir, args.gene_tsv),
        os.path.join(args.custom_dir, args.sample_tsv),
        args.seg
    ]
    for i in range(len(input_paths)):
        input_path = input_paths[i]
        if i<2 and input_path==None:
            continue # elba_schema and upload_config are optional
        elif not os.path.exists(input_path):
            raise OSError("Input path %s does not exist" % input_path)
        if not os.path.isfile(input_path):
            raise OSError("Input path %s is not a regular file or symlink" % input_path)
        elif not os.access(input_path, os.R_OK):
            raise OSError("Input path %s is not readable" % input_path)
    output_paths = [args.out, args.conf, args.log_path]
    for i in range(len(output_paths)):
        out_path = output_paths[i]
        if out_path == None:
            continue # output paths are optional
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
    builder_args = {
        djerba_config_builder.CUSTOM_DIR_INPUT: args.custom_dir,
        djerba_config_builder.GENE_TSV_INPUT: args.gene_tsv,
        djerba_config_builder.SAMPLE_TSV_INPUT: args.sample_tsv,
        djerba_config_builder.MAF_INPUT: args.maf,
        djerba_config_builder.BED_INPUT: args.bed,
        djerba_config_builder.CANCER_TYPE_INPUT: args.cancer_type,
        djerba_config_builder.ONCOKB_INPUT: args.oncokb_token,
        djerba_config_builder.TCGA_INPUT: args.tcga,
        djerba_config_builder.VCF_INPUT: args.vcf,
        djerba_config_builder.SEG_INPUT: args.seg
    }
    djerba_config = djerba_config_builder.build(builder_args)
    if not (args.conf or args.upload or args.upload_config or args.out):
        msg = "No upload or output arguments specified. Exiting without further action."
        print(msg, file=sys.stderr)
        sys.exit(1)
    if args.conf:
        with open(args.conf, 'w') as out:
            out.write(json.dumps(djerba_config, indent=4, sort_keys=True))
    elba_report = report(djerba_config, args.sample_id, args.elba_schema, log_level, args.log_path)
    elba_config = elba_report.get_report_config()
    if args.upload:
        elba_report.upload(elba_config, report_id=args.report_id)
    elif args.upload_config:
        elba_report.upload(elba_config, args.upload_config, args.report_id)
    if args.out:
        elba_report.write(elba_config, args.out, args.force)

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
