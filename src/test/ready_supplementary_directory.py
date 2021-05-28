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

def getMD5(inputPath):
    md5 = hashlib.md5()
    with open(inputPath, 'rb') as f:
        md5.update(f.read())
    return md5.hexdigest()

def get_parser():
     parser = argparse.ArgumentParser(
        description='Ready the supplementary data directory for Djerba. Validates file checksums and writes an updated provenance file.'
    )
     parser.add_argument('-i', '--in', metavar="PATH", required=True, dest='in_dir'
                         help="Directory to validate")
     parser.add_argument('-o', '--out', metavar="PATH", help="Path for modified provenance file; defaults to 'provenance_modified.tsv.gz' in the supplementary data directory")
     parser.add_argument('-v', '--verbose', action="store_true", help="Print results to stdout")

def main(args):
    if not os.path.exists(args.in_dir) and os.path.isdir(args.in_dir):
            raise RuntimeError("Bad supplementary directory: {}".format(args.in_dir))
        # dictionary of relative paths -> md5 sums
        expected = {
            'elba_config_schema.json': '',
            'pass01_panx_provenance.original.tsv.gz': '',
            'S31285117_Regions.bed': '',
            'sequenza/PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip': '',
            'PANX_1249_Lv_M_WG_100-PM-013_LCM5.filter.deduped.realigned.recalibrated.mutect2.tumor_only.filtered.unmatched.DUMMY.maf.gz': '',
            'report_configuration.ini', ''
            'report_configuration_reduced.ini', ''
        }
        for name in expected.keys():
            md5 = self.getMD5(os.path.join(args.in_dir, name))
            if md5 != expected[name]:
                msg = "Checksums do not match for {0}: ".format(name) +\
                    "Found {0}, expected {1}".format(md5, expected[name])
                raise ValueError(msg)
        if args.out:
            provenance_path = args.out
        else:
            provenance_path = os.path.join(args.in_dir, 'provenance_modified.tsv.gz')
        # now use csv and gzip to write the modified provenance path

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())
