"""Search for Djerba inputs"""

# initial proof-of-concept was to find a MAF file from provenance
# TODO expand to other inputs:
# - find files
# - (optionally) link files
# - add file to extraction_config
# - run extractor to get metrics
# - supply metrics (eg. as JSON) to final output

import csv
import gzip
import re

import djerba.simple.constants as constants
import djerba.simple.discover.index as index

class extraction_config:
    """
    Populate a config structure with parameters for data extraction
    """

    def __init__(self, provenance_path, project, donor):
        self.reader = provenance_reader(provenance_path, project, donor)
        self.project = project
        self.donor = donor
        self.params = self._generate_params()

    def _generate_params(self):
        """Generate dictionary of parameters to be stored in a ConfigParser"""
        # TODO may omit some parameters while this class is a work-in-progress
        params = {}
        params[constants.MAFFILE] = self.reader.parse_maf_path()
        params[constants.PATIENTID] = self.donor
        params[constants.SEQUENZAFILE] = self.reader.parse_sequenza_path()
        params[constants.STUDYID] = self.project
        return params

    def get_params(self):
        return self.params

    def update(self, params_for_update, overwrite=False):
        """Update the params dictionary"""
        # TODO validate against a schema before updating?
        if overwrite:
            self.params.update(params_for_update)
        else:
            for key in params_for_update:
                if key in self.params:
                    msg = "Key '{0}' already present in config, overwrite mode not in effect".format(key)
                    raise RuntimeError(msg)
                else:
                    self.params[key] = params_for_update[key]

class provenance_reader:

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

    def _filter_rows(self, index, value, rows=None):
        # find matching provenance rows from a list
        if rows == None: rows = self.provenance
        return filter(lambda x: x[index]==value, rows)

    def _filter_metatype(self, metatype, rows=None):
        return self._filter_rows(index.FILE_META_TYPE, metatype, rows)

    def _filter_pattern(self, pattern, rows=None):
        if rows == None: rows = self.provenance
        return filter(lambda x: re.search(pattern, x[index.FILE_PATH]), rows)

    def _filter_workflow(self, workflow, rows=None):
        return self._filter_rows(index.WORKFLOW_NAME, workflow, rows)

    def _get_most_recent_row(self, rows):
        # if input is empty, raise an error
        # otherwise, return the row with the most recent date field (last in lexical sort order)
        # rows may be an iterator; if so, convert to a list
        rows = list(rows)
        if len(rows)==0:
            raise MissingProvenanceError("No provenance records found")
        return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]

    def _parse_default(self, workflow, metatype, pattern):
        # get most recent file of given workflow, metatype, and file path pattern
        rows = self._filter_workflow(workflow)
        rows = self._filter_metatype(metatype, rows)
        rows = self._filter_pattern(pattern, rows) # metatype usually suffices, but double-check
        row = self._get_most_recent_row(rows)
        return row[index.FILE_PATH]

    def parse_maf_path(self):
        return self._parse_default('variantEffectPredictor', 'application/txt-gz', '\.maf\.gz$')

    def parse_sequenza_path(self):
        return self._parse_default('sequenza', 'application/zip-report-bundle', '_results\.zip$')

class MissingProvenanceError(Exception):
    pass
