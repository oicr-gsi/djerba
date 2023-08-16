"""
Supporting functions to pull files from provenance
"""
import csv
from decimal import Decimal
import logging
import re

import djerba.util.provenance_index as index
import djerba.plugins.tar.sample.constants as constants


def subset_provenance(self, workflow, root_sample_name):
    provenance_location = 'provenance_subset.tsv.gz'
    provenance = []
    try:
        with self.workspace.open_gzip_file(provenance_location) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            for row in reader:
                if row[index.WORKFLOW_NAME] == workflow and row[index.ROOT_SAMPLE_NAME] == root_sample_name:
                    provenance.append(row)
    except OSError as err:
        msg = "Provenance subset file '{0}' not found when looking for {1}".format('provenance_subset.tsv.gz', workflow)
        raise RuntimeError(msg) from err
    return(provenance)

def subset_provenance_sample(self, workflow, group_id, suffix):
    '''Return file path from provenance based on workflow ID, group-id and file suffix'''
    provenance_location = constants.PROVENANCE_OUTPUT
    provenance = []
    joined_group_id = "=".join(("geo_group_id",group_id))
    try:
        with self.workspace.open_gzip_file(provenance_location) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            for row in reader:
                if row[index.WORKFLOW_NAME] == workflow:
                    experiment_name_row = row[index.SAMPLE_ATTRIBUTES].split(";")
                    if experiment_name_row[1] == joined_group_id:
                        provenance.append(row)
    except OSError as err:
        msg = "Provenance subset file '{0}' not found when looking for {1}".format(constants.PROVENANCE_OUTPUT, workflow)
        raise RuntimeError(msg) from err
    try:
        results_path = parse_file_path(self, suffix, provenance)
    except OSError as err:
        msg = "File from workflow {0} with extension {1} was not found in Provenance subset file '{2}' not found".format(workflow, self.RESULTS_SUFFIX,constants.PROVENANCE_OUTPUT)
        raise RuntimeError(msg) from err
    return(results_path)

def parse_file_path(self, file_pattern, provenance):
    # get most recent file of given file path pattern,
    iterrows = _filter_file_path(self, file_pattern, rows=provenance)
    try:
        row = _get_most_recent_row(self, iterrows)
        path = row[index.FILE_PATH]
    except MissingProvenanceError as err:
        msg = "No provenance records meet filter criteria: path-regex = {0}.".format(file_pattern)
        self.logger.debug(msg)
        path = None
    return path

def _filter_file_path(self, pattern, rows):
    return filter(lambda x: re.search(pattern, x[index.FILE_PATH]), rows)

def _get_most_recent_row(self, rows):
    # if input is empty, raise an error
    # otherwise, return the row with the most recent date field (last in lexical sort order)
    # rows may be an iterator; if so, convert to a list
    rows = list(rows)
    if len(rows)==0:
        msg = "Empty input to find most recent row; no rows meet filter criteria?"
        self.logger.debug(msg)
        raise MissingProvenanceError(msg)
    else:
        return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]

class MissingProvenanceError(Exception):
    pass
