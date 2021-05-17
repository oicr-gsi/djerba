"""Search for Djerba inputs"""

# proof-of-concept -- find a MAF file from provenance

# TODO:
# - find MAF file
# - (optionally) link file
# - add file to INI (or other config) for preprocessor
# - preprocess file to extract MAF metrics
# - supply metrics (eg. as JSON) to final output

# TODO write or update INI config for extractor; then extract eg. MAF metrics

import csv
import gzip
import re
import djerba.simple.discover.index as index

class searcher:

    def __init__(self, provenance_path, project, donor):
        # get provenance for the project and donor
        # if this proves to be too slow, can preprocess the file using zgrep
        self.provenance = []
        with gzip.open(provenance_path, 'rt') as infile:
            reader = csv.reader(infile, delimiter="\t")
            for row in reader:
                if row[index.STUDY_TITLE] == project and \
                   row[index.ROOT_SAMPLE_NAME] == donor and \
                   row[index.SEQUENCER_RUN_PLATFORM_ID] != 'Illumina_MiSeq':
                    self.provenance.append(row)

    def _get_most_recent_row(self, rows):
        # return the row with the most recent date field (last in lexical sort order)
        return sorted(rows, key=lambda row: row[0], reverse=True)[0]

    def _parse_rows(self, workflow, file_pattern):
        # get matching rows from the provenance array
        # file_pattern = regex pattern for file path
        i = index.WORKFLOW_NAME
        j = index.FILE_PATH
        return filter(lambda x: x[i]==workflow and re.search(file_pattern, x[j]), self.provenance)

    def parse_maf_path(self):
        # TODO raise an error if no rows are found
        rows = self._parse_rows('variantEffectPredictor', '\.maf\.gz$')
        i = index.WORKFLOW_RUN_SWID
        row = self._get_most_recent_row(filter(lambda x: not re.search('tumor_only', x[i]), rows))
        return row[index.FILE_PATH]
