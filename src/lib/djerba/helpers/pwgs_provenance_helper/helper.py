"""
Helper for writing a subset of file provenance to the shared workspace
"""

import os
import csv
import gzip
import logging
import requests
import json
import re

import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini 
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base
from djerba.util.provenance_reader import provenance_reader, sample_name_container, \
    InvalidConfigurationError
import djerba.plugins.pwgs.constants as pc

class main(helper_base):

    DEFAULT_PROVENANCE_INPUT = '/scratch2/groups/gsi/production/vidarr/'+\
        'vidarr_files_report_latest.tsv.gz'
    PROVENANCE_INPUT_KEY = 'provenance_input_path'
    PROVENANCE_OUTPUT = 'provenance_subset.tsv.gz'
    PRIORITY = 50

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

    def configure(self, config):
        """
        Writes a subset of provenance, and informative JSON files, to the workspace
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        provenance_path = wrapper.get_my_string(self.PROVENANCE_INPUT_KEY)
        work_dir = self.workspace.get_work_dir()
        # Set INI parameters from cardea, if available
        if os.path.exists(os.path.join(work_dir,core_constants.DEFAULT_SAMPLE_INFO)):
            input_data = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            if wrapper.my_param_is_null(pc.PROJECT):
                wrapper.set_my_param(pc.PROJECT, input_data[pc.PROJECT])
            if wrapper.my_param_is_null(pc.DONOR):
                wrapper.set_my_param(pc.DONOR, input_data[pc.DONOR])
            if wrapper.my_param_is_null(pc.PROVENANCE_ID):
                wrapper.set_my_param(pc.PROVENANCE_ID, input_data[pc.PROVENANCE_ID])
        else:
            msg = "Sample Info JSON does not exist. Parameters must be set manually."
            self.logger.warning(msg)
        project = wrapper.get_my_string(pc.PROJECT) 
        donor = wrapper.get_my_string(pc.DONOR)
        # Write Provenance subset, if it doesn't exist
        if self.workspace.has_file(self.PROVENANCE_OUTPUT):
            cache_path = self.workspace.abs_path(self.PROVENANCE_OUTPUT)
            msg = "Provenance subset cache {0} exists, will not overwrite".format(cache_path)
            self.logger.info(msg)
        else:
            self.logger.info("Writing provenance subset cache to workspace")
            self.write_provenance_subset(project, donor, provenance_path)
        # Make path_info file, if it doesn't exist
        if self.workspace.has_file(core_constants.DEFAULT_PATH_INFO):
            msg = "extract: path info files already in workspace, will not overwrite"
            self.logger.info(msg)
        else:
            mrdetect_file_suffixes = [pc.RESULTS_SUFFIX, pc.VAF_SUFFIX, pc.HBC_SUFFIX, pc.SNV_COUNT_SUFFIX]
            path_info = self.read_provenance_subset("mrdetect", wrapper.get_my_string(pc.PROVENANCE_ID), mrdetect_file_suffixes)
            path_info.update(self.read_provenance_subset("dnaSeqQC",  wrapper.get_my_string(pc.PROVENANCE_ID), [pc.BAMQC_SUFFIX]))
            self.write_path_info(path_info)
        return wrapper.get_config()

    def extract(self, config):
        self.validate_full_config(config)
    
    def parse_file_path(self, file_pattern, provenance):
        # get most recent file of given file path pattern,
        iterrows = self._filter_file_path(file_pattern, rows=provenance)
        try:
            row = self._get_most_recent_row(iterrows)
            path = row[index.FILE_PATH]
        except MissingProvenanceError as err:
            msg = "No provenance records meet filter criteria: path-regex = {0}.".format(file_pattern)
            self.logger.debug(msg)
            path = None
        return path

    def read_provenance_subset(self, workflow, provenance_id, suffixes):
        '''Return file path from provenance based on workflow ID, group-id and file suffix'''
        provenance_location = pc.PROVENANCE_OUTPUT
        # Subset Provenance to only files within the specified workflow
        provenance = []
        try:
            with self.workspace.open_gzip_file(provenance_location) as in_file:
                reader = csv.reader(in_file, delimiter="\t")
                for row in reader:
                    if row[index.WORKFLOW_NAME] == workflow and row[index.SAMPLE_NAME] == provenance_id:
                        provenance.append(row)
        except OSError as err:
            msg = "Provenance subset file '{0}' not found when looking for {1}".format(pc.PROVENANCE_OUTPUT, workflow)
            raise RuntimeError(msg) from err
        # Make path file by matching with file suffixes
        results_path = {}
        for suffix in suffixes:
            try:
                results_path[suffix] = self.parse_file_path(suffix, provenance)
            except OSError as err:
                msg = "File from workflow {0} with extension {1} was not found in Provenance subset file {2}".format("mrdetect", self.RESULTS_SUFFIX, pc.PROVENANCE_OUTPUT)
                raise RuntimeError(msg) from err
        return(results_path)

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default(self.PROVENANCE_INPUT_KEY, self.DEFAULT_PROVENANCE_INPUT)
        discovered = [
            pc.PROJECT,
            pc.DONOR,
            pc.PROVENANCE_ID
        ]
        for key in discovered:
            self.add_ini_discovered(key)

    def write_path_info(self, path_info):
        self.workspace.write_json(core_constants.DEFAULT_PATH_INFO, path_info)
        self.logger.debug("Wrote path info to workspace: {0}".format(path_info))

    def write_provenance_subset(self, study, donor, provenance_path):
        self.logger.info('Started reading file provenance from {0}'.format(provenance_path))
        total = 0
        kept = 0
        with gzip.open(provenance_path, 'rt') as in_file, \
             self.workspace.open_gzip_file(self.PROVENANCE_OUTPUT, write=True) as out_file:
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            for row in reader:
                total += 1
                if total % 100000 == 0:
                    self.logger.debug("Read {0} input rows".format(total))
                if row[index.STUDY_TITLE] == study and row[index.ROOT_SAMPLE_NAME] == donor:
                    writer.writerow(row)
                    kept += 1
        self.logger.info('Done reading FPR; kept {0} of {1} rows'.format(kept, total))
        self.logger.debug('Wrote provenance subset to {0}'.format(self.PROVENANCE_OUTPUT))
    
class MissingProvenanceError(Exception):
    pass
