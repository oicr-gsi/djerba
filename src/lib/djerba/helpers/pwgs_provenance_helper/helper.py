"""
Helper for writing a subset of file provenance to the shared workspace

Outputs to the workspace:
- Subset of sample provenance for the donor and study supplied by the user
- JSON file with donor, study, and sample names

Plugins can then create their own provenance reader objects using params in the JSON, to
find relevant file paths. Reading the provenance subset is very much faster than reading 
the full file provenance report.
"""

import os
import csv
import gzip
import logging
import requests
import json
import re

import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini  # TODO new module for these constants?
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base
import djerba.util.input_params_tools as input_params_tools
from djerba.util.provenance_reader import provenance_reader, sample_name_container, \
    InvalidConfigurationError
import djerba.plugins.pwgs.constants as pc

class main(helper_base):

    DEFAULT_CARDEA_URL='https://cardea.gsi.oicr.on.ca/requisition-cases'
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
        cardea_url = wrapper.get_my_string('cardea_url')
        requisition_id = wrapper.get_my_string('requisition_id')
        input_data = input_params_tools.get_input_params_json(self)
        if input_data == None:
            msg = "Input params JSON does not exist. Parameters must be set manually."
            self.logger.warning(msg)
        sample_info = self.get_cardea(requisition_id, cardea_url)
        study = sample_info['project_id']
        donor = sample_info['root_id']
        if self.workspace.has_file(self.PROVENANCE_OUTPUT):
            self.logger.debug("Provenance subset cache exists, will not overwrite")
        else:
            self.logger.info("Writing provenance subset cache to workspace")
            self.write_provenance_subset(study, donor, provenance_path)
        ## write sample_info.json; populate sample names from provenance if needed
        group_id = sample_info['group_id']
        suffixes = [pc.RESULTS_SUFFIX, pc.VAF_SUFFIX, pc.HBC_SUFFIX]
        path_info = self.subset_provenance("mrdetect", group_id, suffixes)
        self.write_path_info(path_info)
        keys = [core_constants.TUMOUR_ID]
        keys.extend(self.SAMPLE_NAME_KEYS)
        for key in keys:
            #value = sample_info.get(key)
            if wrapper.my_param_is_null(key):
                if value == None:
                    msg = "No value found in provenance for parameter '{0}'; ".format(key)+\
                        "can manually specify value in config and re-run"
                    self.logger.error(msg)
                    raise DjerbaProvenanceError(msg)
                else:
                    wrapper.set_my_param(key, value)
            elif value == None:
                value = wrapper.get_my_string(key)
                msg = "Overwriting null value for '{0}' in sample info ".format(key)+\
                    "with user-defined value '{0}'".format(value)
                self.logger.debug(msg)
                sample_info[key] = value
        # Write updated sample info as JSON
        self.write_sample_info(sample_info)
        return wrapper.get_config()

    def extract(self, config):
        """
        If not already in the workspace, write the provenance subset and sample info JSON
        """
        self.validate_full_config(config)
        wrapper = self.get_config_wrapper(config)
        provenance_path = wrapper.get_my_string(self.PROVENANCE_INPUT_KEY)
        study = wrapper.get_my_string(self.STUDY_TITLE)
        donor = wrapper.get_my_string(self.ROOT_SAMPLE_NAME)
        if self.workspace.has_file(self.PROVENANCE_OUTPUT):
            cache_path = self.workspace.abs_path(self.PROVENANCE_OUTPUT)
            msg = "Provenance subset cache {0} exists, will not overwrite".format(cache_path)
            self.logger.info(msg)
        else:
            self.logger.info("Writing provenance subset cache to workspace")
            self.write_provenance_subset(study, donor, provenance_path)
        if self.workspace.has_file(core_constants.DEFAULT_SAMPLE_INFO) and \
           self.workspace.has_file(core_constants.DEFAULT_PATH_INFO):
            msg = "extract: sample/path info files already in workspace, will not overwrite"
            self.logger.info(msg)
        else:
            samples = self.get_sample_name_container(wrapper)
            sample_info, path_info = self.read_provenance(study, donor, samples)
            if not self.workspace.has_file(core_constants.DEFAULT_SAMPLE_INFO):
                self.logger.debug('extract: writing sample info')
                self.write_sample_info(sample_info)
            if not self.workspace.has_file(core_constants.DEFAULT_PATH_INFO):
                self.logger.debug('extract: writing path info')
                self.write_path_info(path_info)

    def get_cardea(self, requisition_id, cardea_url):
        url = "/".join((cardea_url,requisition_id))
        r = requests.get(url, allow_redirects=True)
        requisition_json = json.loads(r.text)
        #TODO: add check that you actually found something, 'status' != 404
        for case in requisition_json['cases']:
            #TODO: add check that there is data
            requisition = case["requisition"]
            projects = case["projects"]
        for qc_group in requisition['qcGroups']:
            group_id = qc_group['groupId']
            root_id = qc_group['donor']['name']
            patient_id = qc_group['donor']['externalName']
        for project in projects:
            project_id = project["name"]
        requisition_info = {
            'assay_name' : requisition_json["assayName"],
            'project': project_id,
            'donor': root_id,
            'patient_study_id': patient_id,
            'group_id': group_id,
        }
        return(requisition_info)
    
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

    def subset_provenance(self, workflow, group_id, suffixes):
        '''Return file path from provenance based on workflow ID, group-id and file suffix'''
        provenance_location = pc.PROVENANCE_OUTPUT
        provenance = []
        try:
            with self.workspace.open_gzip_file(provenance_location) as in_file:
                reader = csv.reader(in_file, delimiter="\t")
                for row in reader:
                    if row[index.WORKFLOW_NAME] == workflow and row[index.SAMPLE_NAME] == group_id:
                        provenance.append(row)
        except OSError as err:
            msg = "Provenance subset file '{0}' not found when looking for {1}".format(pc.PROVENANCE_OUTPUT, workflow)
            raise RuntimeError(msg) from err
        for suffix in suffixes:
            try:
                results_path = {suffix: self.parse_file_path(suffix, provenance)}
            except OSError as err:
                msg = "File from workflow {0} with extension {1} was not found in Provenance subset file '{2}' not found".format("mrdetect", self.RESULTS_SUFFIX, pc.PROVENANCE_OUTPUT)
                raise RuntimeError(msg) from err
        return(results_path)

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default(self.PROVENANCE_INPUT_KEY, self.DEFAULT_PROVENANCE_INPUT)
        self.set_ini_default('cardea_url', self.DEFAULT_CARDEA_URL)
        self.add_ini_required('requisition_id')
        self.add_ini_discovered(self.STUDY_TITLE)
        self.add_ini_discovered(self.ROOT_SAMPLE_NAME)
        self.add_ini_discovered(ini.SAMPLE_NAME_WG_T)
        self.add_ini_discovered(core_constants.TUMOUR_ID)

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

    def write_sample_info(self, sample_info):
        self.workspace.write_json(core_constants.DEFAULT_SAMPLE_INFO, sample_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(sample_info))
    
class MissingProvenanceError(Exception):
    pass

class DjerbaProvenanceError(Exception):
    pass
