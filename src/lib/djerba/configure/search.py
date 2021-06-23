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
import djerba.simple.constants as constants
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
        if len(self.provenance)==0:
            msg = "No provenance records found for project '%s' and donor '%s'" % (project, donor)
            raise MissingProvenanceError(msg)

    def _get_most_recent_row(self, rows):
        # if input is empty, raise an error
        # otherwise, return the row with the most recent date field (last in lexical sort order)
        if len(rows)==0:
            raise MissingProvenanceError("No provenance records found")
        return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]

    def _parse_rows(self, workflow, file_pattern):
        # get matching rows from the provenance array
        # file_pattern = regex pattern for file path
        i = index.WORKFLOW_NAME
        j = index.FILE_PATH
        return filter(lambda x: x[i]==workflow and re.search(file_pattern, x[j]), self.provenance)

    def parse_maf_path(self):
        rows = list(filter(
            lambda x: not re.search('tumor_only', x[index.WORKFLOW_RUN_SWID]),
            self._parse_rows('variantEffectPredictor', '\.maf\.gz$')
        ))
        row = self._get_most_recent_row(rows)
        return row[index.FILE_PATH]

    def update_config(self, config):
        """Update provenance fields in a config object"""
        config[constants.CONFIG_HEADER][constants.MAF_FILE] = self.parse_maf_path()
        return config

class MissingProvenanceError(Exception):
    pass
