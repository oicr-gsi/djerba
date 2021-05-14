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
import re

class searcher:

    TMP_PROVENANCE_FILENAME = 'provenance_subset.tsv'
    
    def __init__(self, provenance_path, project, donor):
        # get provenance for the project and donor
        # if this proves to be too slow, can preprocess the file using zgrep
        self.provenance = []
        with gzip.open(provenance_path, 'rt') as infile:
            reader = csv.reader(infile, delimiter="\t")
            for row in reader:
                if row[1] == project and row[7] == donor and row[22] != 'Illumina_MiSeq':
                    self.provenance.append(row)

    def _get_most_recent_row(self, rows):
        # return the row with the most recent date field (last in lexical sort order)
        return sorted(rows, key=lambda row: row[0], reverse=True)[0]

    def _parse_rows(self, workflow, suffix):
        # get matching rows from the provenance array
        # suffix = suffix of file path
        return [x for x in self.provenance if x[30]==workflow and re.search(suffix, x[46])]

    def parse_maf_path(self):
        # TODO raise an error if no rows are found
        rows = self._parse_rows('variantEffectPredictor', '\.maf\.gz$')
        row = self._get_most_recent_row([x for x in rows if not re.search('tumor_only', x[37])])
        return row[46]
