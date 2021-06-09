#! /usr/bin/env python3

"""
Validate the supplementary test data directory:
- Directory contains files not appropriate for github, eg. non-public data
- Ensure required files are present and checksums match
- Modify provenance so relevant paths point to the supplementary directory
"""

import argparse
import csv
import gzip
import hashlib
import os
import sys

def getMD5(inputPath):
    md5 = hashlib.md5()
    with open(inputPath, 'rb') as f:
        md5.update(f.read())
    return md5.hexdigest()

def get_parser():
     parser = argparse.ArgumentParser(
        description='Ready the supplementary data directory for Djerba. Validates file checksums and writes an updated provenance file.'
    )
     parser.add_argument('-i', '--in', metavar="PATH", required=True, dest='in_dir',
                         help="Directory to validate")
     parser.add_argument('-o', '--out', metavar="PATH", required=True, help="Path for modified provenance file")
     parser.add_argument('-v', '--verbose', action="store_true", help="Print results to stdout")
     return parser

def main(args):
    in_dir = os.path.realpath(args.in_dir)
    if not os.path.isdir(in_dir):
            raise OSError("Path '{0}' is not a directory".format(in_dir))
    # dictionary of relative paths -> md5 sums
    expected = {
        'elba_config_schema.json': '591eff214424d8a9216960cb89d62738',
        'mavis_summary_all_WG.PANX.1249.Lv.M.100-PM-013.LCM5_WT.PANX.1249.Lv.M.100-PM-013.LCM5.tab': 'e5b148e6dee1b4a46ecabc7e05239cc5',
        'pass01_panx_provenance.original.tsv.gz': 'd1909b18d00d6d2531f3ff939ba03716',
        'S31285117_Regions.bed': 'd6b2700955084e39161fd345145f328e',
        'sequenza/PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip': '6a95febce31ac8e6ede8927f2a5e7937',
        'PANX_1249_Lv_M_WG_100-PM-013_LCM5.filter.deduped.realigned.recalibrated.mutect2.tumor_only.filtered.unmatched.DUMMY.maf.gz': '1b1d47cc56518e1818c4146273a663dd',
        'report_configuration.ini': 'e03e6f839d1a2699c7d5ad1c61a239d7',
        'report_configuration_reduced.ini': '816e60589071bc20e90efe425a463a20'
    }
    for name in expected.keys():
        in_path = os.path.join(in_dir, name)
        if not (os.path.isfile(in_path)):
            raise OSError("Path '{0}' is not a file: ".format(in_path))
        elif getMD5(in_path) != expected[name]:
            msg = "Checksums do not match for {0}: ".format(name)+\
                "Found {0}, expected {1}".format(getMD5(in_path), expected[name])
            raise ValueError(msg)
    if args.verbose:
        print("MD5 sums match for all expected inputs")
    # now use csv and gzip to write the modified provenance path
    # we modify file paths for data that is read in tests
    provenance_path = args.out
    new_paths = {
        '/oicr/data/archive/seqware/seqware_analysis_12/hsqwprod/seqware-results/sequenza_2.1/21562306/PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip': os.path.join(in_dir, 'sequenza', 'PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip'),
        '/oicr/data/archive/seqware/seqware_analysis_12/hsqwprod/seqware-results/variantEffectPredictor_2.0.2/21783975/PANX_1249_Lv_M_WG_100-PM-013_LCM5.filter.deduped.realigned.recalibrated.mutect2.tumor_only.filtered.unmatched.maf.gz': os.path.join(in_dir, 'PANX_1249_Lv_M_WG_100-PM-013_LCM5.filter.deduped.realigned.recalibrated.mutect2.tumor_only.filtered.unmatched.DUMMY.maf.gz')
    }
    with gzip.open(os.path.join(in_dir, 'pass01_panx_provenance.original.tsv.gz'), 'rt') as in_file, gzip.open(args.out, 'wt') as out_file:
        reader = csv.reader(in_file, delimiter="\t")
        writer = csv.writer(out_file, delimiter="\t")
        for row in reader:
            for key in new_paths.keys():
                if row[46]==key:
                    row[46] = new_paths[key]
            writer.writerow(row)
    if args.verbose:
        print("Wrote modified provenance file to {0}".format(args.out))

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
