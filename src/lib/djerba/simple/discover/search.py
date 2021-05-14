"""Search for Djerba inputs"""

# proof-of-concept -- find a MAF file from provenance

# TODO:
# - find MAF file
# - (optionally) link file
# - add file to INI (or other config) for preprocessor
# - preprocess file to extract MAF metrics
# - supply metrics (eg. as JSON) to final output

import csv
import gzip
import os
import re
import subprocess
import tempfile
import time
import pandas as pd

class searcher:

    TMP_PROVENANCE_FILENAME = 'provenance_subset.tsv'
    
    def __init__(self, provenance_path, project, donor, analysis_unit):
        tmp = tempfile.TemporaryDirectory(prefix='djerba_simple_')
        #tmp_provenance_path = os.path.join(tmp.name, self.TMP_PROVENANCE_FILENAME)
        tmp_provenance_path = '/home/iain/tmp/djerba/test/provenance.tsv'
        # get provenance for the project and donor
        # using csv for simple one-off read/write; pandas for multiple, complex queries
        # if this proves to be too slow, can preprocess the file using zgrep

        self.provenance = []
        with gzip.open(provenance_path, 'rt') as infile, open(tmp_provenance_path, 'w') as outfile:
            reader = csv.reader(infile, delimiter="\t")
            writer = csv.writer(outfile, delimiter="\t")
            for row in reader:
                if row[1] == project and row[7] == donor and row[22] != 'Illumina_MiSeq':
                    self.provenance.append(row)

        # TODO make the headers path portable
        headers_path = '/home/iain/oicr/git/djerba/src/lib/djerba/simple/data/headers.tsv'
        with open(headers_path) as headers_file:
            headers = next(csv.reader(headers_file, delimiter="\t"))
        self.provenance = pd.read_csv(tmp_provenance_path, sep="\t", header=0, names=headers)
        with open('/home/iain/tmp/pandas.txt', 'w') as out:
            print(self.provenance, file=out)
        tmp.cleanup()

    def _matches_analysis_unit(self, row, analysis_unit):
        match = False
        for index in [12, 17, 37, 46]:
            if re.search(analysis_unit, row[index]):
                match = True
                break
        print("AU", match)
        return match

    def _matches_params(self, row, project, donor):
        match = \
            row[1] == project and \
            row[7] == donor and \
            row[22] != 'Illumina_MiSeq' and \
            self._matches_analysis_unit(row, analysis_unit)
        return match

    def _parse_rows(self, analysis_unit, workflow, suffix):
        # get the desired path from the provenance dataframe
        # exclude is a list of [column, pattern] pairs; reject if a match is found
        # suffix = suffix of file path
        # note that columns are zero-indexed in pandas
        # if multiple results, sort and return one?
        # useful 1-indexed provenance columns:
        # 31 = workflow
        # 38 = tumor_only
        # 13,18,38,47 = analysis_unit??

        #has_au = self._make_analysis_unit_checker(analysis_unit)
        df = self.provenance

        df = df.loc[df['Workflow Name']==workflow]
        df = df.loc[df['File Path'].str.contains(suffix)]
        cols = ['Parent Sample Attributes', 'Sample Attributes', 'Workflow Run Attributes', 'File Path']
        for col in cols:
            df = df.loc[df[col].str.contains(analysis_unit)]
        return df

    def parse_maf_path(self, analysis_unit):
        #df = self._parse_rows(analysis_unit, 'variantEffectPredictor', '\.maf\.gz$', [[37, 'tumor_only']])
        df = self._parse_rows(analysis_unit, 'variantEffectPredictor', '\.maf\.gz$')
        #df = df.loc[not re.search('tumor_only', df['Workflow Run Attributes'])]
        print(df)
