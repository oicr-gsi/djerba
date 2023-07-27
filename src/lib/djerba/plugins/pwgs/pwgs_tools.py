"""pwgs supporting functions"""
import csv
from decimal import Decimal
import logging
import re

import djerba.plugins.pwgs.constants as constants
import djerba.util.provenance_index as index


def preprocess_results(self, results_path, group_id = 'None'):
    """
    pull data from results file
    """
    if results_path == 'None':
        provenance = subset_provenance(self, "mrdetect", group_id)
        try:
            results_path = parse_file_path(self, self.RESULTS_SUFFIX, provenance)
        except OSError as err:
            msg = "File from workflow {0} with extension {1} was not found in Provenance subset file '{2}' not found".format("mrdetect", self.RESULTS_SUFFIX,constants.PROVENANCE_OUTPUT)
            raise RuntimeError(msg) from err
    results_dict = {}
    with open(results_path, 'r') as results_file:
        reader_file = csv.reader(results_file, delimiter="\t")
        next(reader_file, None)
        for row in reader_file:
            try:
                results_dict = {
                                'TF': float('%.1E' % Decimal(row[7]))*100,
                                'pvalue':  float('%.3E' % Decimal(row[10]))
                                }
            except IndexError as err:
                msg = "Incorrect number of columns in vaf row: '{0}' ".format(row)+\
                        "read from '{0}'".format(results_path)
                raise RuntimeError(msg) from err
    if results_dict['pvalue'] > float(constants.DETECTION_ALPHA) :
        significance_text = "not significantly larger"
        results_dict['outcome'] = "UNDETECTED"
        results_dict['TF'] = 0
    elif results_dict['pvalue'] <= float(constants.DETECTION_ALPHA):
        significance_text = "significantly larger"
        results_dict['outcome'] = "DETECTED"
    else:
        msg = "results pvalue {0} incompatible with detection alpha {1}".format(results_dict['pvalue'], constants.DETECTION_ALPHA)
        self.logger.error(msg)
        raise RuntimeError
    results_dict['significance_text'] = significance_text
    results_dict['results_path'] = results_path
    return results_dict

def subset_provenance(self, workflow, group_id):
    provenance_location = constants.PROVENANCE_OUTPUT
    provenance = []
    try:
        with self.workspace.open_gzip_file(provenance_location) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            for row in reader:
                if row[index.WORKFLOW_NAME] == workflow and row[index.SAMPLE_NAME] == group_id:
                    provenance.append(row)
    except OSError as err:
        msg = "Provenance subset file '{0}' not found when looking for {1}".format(constants.PROVENANCE_OUTPUT, workflow)
        raise RuntimeError(msg) from err
    return(provenance)

def parse_file_path(self, file_pattern, provenance):
    # get most recent file of given workflow, metatype, file path pattern, and sample name
    # self._filter_* functions return an iterator
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
