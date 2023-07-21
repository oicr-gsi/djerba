"""Helper for writing a subset of file provenance to the shared workspace"""

import csv
import gzip
import logging
import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini  # TODO new module for these constants?
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base
from djerba.util.provenance_reader import provenance_reader, sample_name_container, \
    InvalidConfigurationError

class main(helper_base):

    DEFAULT_PROVENANCE_INPUT = '/scratch2/groups/gsi/production/vidarr/'+\
        'vidarr_files_report_latest.tsv.gz'
    PROVENANCE_INPUT_KEY = 'provenance_input_path'
    STUDY_TITLE = 'study_title'
    ROOT_SAMPLE_NAME = 'root_sample_name'
    PROVENANCE_OUTPUT = 'provenance_subset.tsv.gz'
    PRIORITY = 50
    SAMPLE_NAME_KEYS = [
        ini.SAMPLE_NAME_WG_N,
        ini.SAMPLE_NAME_WG_T,
        ini.SAMPLE_NAME_WT_T
    ]
    
    def configure(self, config):
        """
        Writes a subset of provenance, and a sample info JSON file, to the workspace
        """
        # TODO This helper could also write relevant file paths as JSON. Alternatively,
        # other components can create their own provenance readers, using the provenance
        # subset file and study/donor/sample parameters in the sample info JSON.
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        provenance_path = wrapper.get_my_string(self.PROVENANCE_INPUT_KEY)
        study = wrapper.get_my_string(self.STUDY_TITLE)
        donor = wrapper.get_my_string(self.ROOT_SAMPLE_NAME)
        self.write_provenance_subset(study, donor, provenance_path)
        # write sample_info.json; populate sample names from provenance if needed
        samples = self.get_sample_name_container(wrapper)
        info = self.read_sample_info(study, donor, samples)
        self.write_sample_info(info)
        for key in self.SAMPLE_NAME_KEYS:
            wrapper.set_my_param(key, info.get(key))
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
            msg = "extract: {0} ".format(self.PROVENANCE_OUTPUT)+\
                "already in workspace, will not overwrite"
            self.logger.debug(msg)
        else:
            self.write_provenance_subset(study, donor, provenance_path)
        if self.workspace.has_file(core_constants.DEFAULT_SAMPLE_INFO):
            msg = "extract: {0} ".format(core_constants.DEFAULT_SAMPLE_INFO)+\
                "already in workspace, will not overwrite"
            self.logger.debug(msg)
        else:
            samples = self.get_sample_name_container(wrapper)
            info = self.read_sample_info(study, donor, samples)
            self.write_sample_info(info)

    def get_sample_name_container(self, config_wrapper):
        """
        Populate a sample name container for input to the file provenance reader
        Allowed configurations:
        - All values null
        - All values specified
        - WG tumour/normal names specified, WT name null
        """
        samples = sample_name_container()
        if config_wrapper.my_param_is_not_null(ini.SAMPLE_NAME_WG_N):
            samples.set_wg_n(config_wrapper.get_my_string(ini.SAMPLE_NAME_WG_N))
        if config_wrapper.my_param_is_not_null(ini.SAMPLE_NAME_WG_T):
            samples.set_wg_t(config_wrapper.get_my_string(ini.SAMPLE_NAME_WG_T))
        if config_wrapper.my_param_is_not_null(ini.SAMPLE_NAME_WT_T):
            samples.set_wt_t(config_wrapper.get_my_string(ini.SAMPLE_NAME_WT_T))
        if samples.is_valid():
            self.logger.debug("Sample names from INI are valid: {0}".format(samples))
        else:
            msg = "Invalid sample name configuration: {0}.".format(samples)
            msg = msg + " Must either be empty, or have at least WG tumour/normal names"
            self.logger.error(msg)
            raise InvalidConfigurationError(msg)
        return samples

    def read_sample_info(self, study, donor, samples):
        """
        Parse file provenance and populate the sample info data structure
        If the sample names are unknown, get from file provenance given study and donor
        """        
        subset_path = self.workspace.abs_path(self.PROVENANCE_OUTPUT)
        reader = provenance_reader(subset_path, study, donor, samples)
        names = reader.get_sample_names()
        ids = reader.get_identifiers()
        sample_info = {
            self.STUDY_TITLE: study,
            self.ROOT_SAMPLE_NAME: donor,
            core_constants.TUMOUR_ID: ids.get(ini.TUMOUR_ID),
            core_constants.NORMAL_ID: ids.get(ini.NORMAL_ID),
            ini.SAMPLE_NAME_WG_T: names.get(ini.SAMPLE_NAME_WG_T),
            ini.SAMPLE_NAME_WG_N: names.get(ini.SAMPLE_NAME_WG_N),
            ini.SAMPLE_NAME_WT_T: names.get(ini.SAMPLE_NAME_WT_T)
        }
        return sample_info

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default(self.PROVENANCE_INPUT_KEY, self.DEFAULT_PROVENANCE_INPUT)
        self.add_ini_required(self.STUDY_TITLE)
        self.add_ini_required(self.ROOT_SAMPLE_NAME)
        self.set_ini_null_default(ini.SAMPLE_NAME_WG_N)
        self.set_ini_null_default(ini.SAMPLE_NAME_WG_T)
        self.set_ini_null_default(ini.SAMPLE_NAME_WT_T)

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
        self.logger.debug('Done reading FPR; kept {0} of {1} rows'.format(kept, total))
        self.logger.info('Finished reading file provenance from {0}'.format(provenance_path))
        self.logger.debug('Wrote provenance subset to {0}'.format(self.PROVENANCE_OUTPUT))

    def write_sample_info(self, sample_info):
        self.workspace.write_json(core_constants.DEFAULT_SAMPLE_INFO, sample_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(sample_info))
