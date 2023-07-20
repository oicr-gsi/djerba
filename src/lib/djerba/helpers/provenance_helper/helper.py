"""Helper for writing a subset of file provenance to the shared workspace"""

import csv
import gzip
import logging
import djerba.core.constants as core_constants
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

    # constants previously in ini_fields.py
    NORMAL_ID = 'normalid'
    TUMOUR_ID = 'tumourid'
    PATIENT_ID = 'patientid'
    SAMPLE_NAME_WG_N = 'sample_name_whole_genome_normal' # whole genome, normal
    SAMPLE_NAME_WG_T = 'sample_name_whole_genome_tumour' # whole genome, tumour
    SAMPLE_NAME_WT_T = 'sample_name_whole_transcriptome' # whole transcriptome, tumour
    
    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        provenance_path = wrapper.get_my_string(self.PROVENANCE_INPUT_KEY)
        study = wrapper.get_my_string(self.STUDY_TITLE)
        donor = wrapper.get_my_string(self.ROOT_SAMPLE_NAME)
        self.write_provenance_subset(study, donor, provenance_path)      
        self.logger.debug("configure: Wrote provenance subset to workspace")
        # parse the file provenance subset and write sample_info.json to the workspace
        samples = sample_name_container()
        if wrapper.my_param_is_not_null(self.SAMPLE_NAME_WG_N):
            samples.set_wg_n(wrapper.get_my_string(self.SAMPLE_NAME_WG_N))
        if wrapper.my_param_is_not_null(self.SAMPLE_NAME_WG_T):
            samples.set_wg_t(wrapper.get_my_string(self.SAMPLE_NAME_WG_T))
        if wrapper.my_param_is_not_null(self.SAMPLE_NAME_WT_T):
            samples.set_wt_t(wrapper.get_my_string(self.SAMPLE_NAME_WT_T))
        if samples.is_valid():
            self.logger.debug("Sample names from INI are valid: {0}".format(samples))
        else:
            msg = "Invalid sample name configuration: {0}.".format(samples)
            msg = msg + " Must either be empty, or have at least WG tumour/normal names"
            self.logger.error(msg)
            raise InvalidConfigurationError(msg)
        # get canonical names from the file provenance reader
        names = self.write_sample_info(study, donor, samples)
        self.logger.debug("configure: Wrote sample info to workspace")
        for key in names.keys():
            wrapper.set_my_param(key, names.get(key))
        return wrapper.get_config()
    
    def extract(self, config):
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
            self.logger.debug("extract: Wrote provenance subset to workspace")

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_ini_default(self.PROVENANCE_INPUT_KEY, self.DEFAULT_PROVENANCE_INPUT)
        self.add_ini_required(self.STUDY_TITLE)
        self.add_ini_required(self.ROOT_SAMPLE_NAME)
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_null_default(self.SAMPLE_NAME_WG_N)
        self.set_ini_null_default(self.SAMPLE_NAME_WG_T)
        self.set_ini_null_default(self.SAMPLE_NAME_WT_T)

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

    def write_sample_info(self, study, donor, samples):
        subset_path = self.workspace.abs_path(self.PROVENANCE_OUTPUT)
        reader = provenance_reader(subset_path, study, donor, samples)
        names = reader.get_sample_names()
        ids = reader.get_identifiers()
        # TODO should the tumour/normal IDs be INI parameters?
        sample_info = {
            self.STUDY_TITLE: study,
            self.ROOT_SAMPLE_NAME: donor,
            core_constants.TUMOUR_ID: ids.get(self.TUMOUR_ID),
            core_constants.NORMAL_ID: ids.get(self.NORMAL_ID),
            self.SAMPLE_NAME_WG_T: names.get(self.SAMPLE_NAME_WG_T),
            self.SAMPLE_NAME_WG_N: names.get(self.SAMPLE_NAME_WG_N),
            self.SAMPLE_NAME_WT_T: names.get(self.SAMPLE_NAME_WT_T)
        }
        self.workspace.write_json(core_constants.DEFAULT_SAMPLE_INFO, sample_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(sample_info))
        return names
