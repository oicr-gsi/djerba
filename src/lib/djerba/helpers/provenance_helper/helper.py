"""
Helper for writing a subset of file provenance to the shared workspace

Outputs to the workspace:
- Subset of sample provenance for the donor and study supplied by the user
- JSON file with donor, study, and sample names

Plugins can then create their own provenance reader objects using params in the JSON, to
find relevant file paths. Reading the provenance subset is very much faster than reading 
the full file provenance report.
"""

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

    # identifiers for bam/bai files
    WG_N_BAM = 'whole genome normal bam'
    WG_N_IDX = 'whole genome normal bam index'
    WG_T_BAM = 'whole genome tumour bam'
    WG_T_IDX = 'whole genome tumour bam index'
    WT_T_BAM = 'whole transcriptome tumour bam'
    WT_T_IDX = 'whole transcriptome tumour bam index'

    def configure(self, config):
        """
        Writes a subset of provenance, and a sample info JSON file, to the workspace
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        provenance_path = wrapper.get_my_string(self.PROVENANCE_INPUT_KEY)
        study = wrapper.get_my_string(self.STUDY_TITLE)
        donor = wrapper.get_my_string(self.ROOT_SAMPLE_NAME)
        self.write_provenance_subset(study, donor, provenance_path)
        # write sample_info.json; populate sample names from provenance if needed
        samples = self.get_sample_name_container(wrapper)
        sample_info, path_info = self.read_provenance(study, donor, samples)
        self.write_sample_info(sample_info)
        self.write_path_info(path_info)
        for key in self.SAMPLE_NAME_KEYS:
            wrapper.set_my_param(key, sample_info.get(key))
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
            self.logger.info(msg)
        else:
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

    def read_provenance(self, study, donor, samples):
        """
        Parse file provenance and populate the sample info data structure
        If the sample names are unknown, get from file provenance given study and donor
        Also populate a data structure with workflow outputs (if available)
        """
        subset_path = self.workspace.abs_path(self.PROVENANCE_OUTPUT)
        reader = provenance_reader(
            subset_path,
            study,
            donor,
            samples,
            log_level=self.log_level,
            log_path=self.log_path
        )
        names = reader.get_sample_names()
        ids = reader.get_identifiers()
        sample_info = {
            self.STUDY_TITLE: study,
            self.ROOT_SAMPLE_NAME: donor,
            core_constants.PATIENT_STUDY_ID: ids.get(ini.PATIENT_ID),
            core_constants.TUMOUR_ID: ids.get(ini.TUMOUR_ID),
            core_constants.NORMAL_ID: ids.get(ini.NORMAL_ID),
            ini.SAMPLE_NAME_WG_T: names.get(ini.SAMPLE_NAME_WG_T),
            ini.SAMPLE_NAME_WG_N: names.get(ini.SAMPLE_NAME_WG_N),
            ini.SAMPLE_NAME_WT_T: names.get(ini.SAMPLE_NAME_WT_T)
        }
        # find paths of workflow outputs; values may be None
        path_info = {
            reader.WF_ARRIBA: reader.parse_arriba_path(),
            reader.WF_BMPP: {
                self.WG_T_BAM: reader.parse_wg_bam_path(),
                self.WG_T_IDX: reader.parse_wg_index_path(),
                self.WG_N_BAM: reader.parse_wg_bam_ref_path(),
                self.WG_N_IDX: reader.parse_wg_index_ref_path()
            },
            reader.WF_DELLY: reader.parse_delly_path(),
            reader.WF_MAVIS: reader.parse_mavis_path(),
            reader.WF_MRDETECT: reader.parse_mrdetect_path(),
            reader.WF_MSISENSOR: reader.parse_msi_path(),
            reader.WF_RSEM: reader.parse_gep_path(),
            reader.WF_SEQUENZA: reader.parse_sequenza_path(),
            reader.WF_STAR: {
                self.WT_T_BAM: reader.parse_wt_bam_path(),
                self.WT_T_IDX: reader.parse_wt_index_path()
            },
            reader.WF_STARFUSION: reader.parse_starfusion_predictions_path(),
            reader.WF_VEP: reader.parse_maf_path()
        }
        return sample_info, path_info

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default(self.PROVENANCE_INPUT_KEY, self.DEFAULT_PROVENANCE_INPUT)
        self.add_ini_required(self.STUDY_TITLE)
        self.add_ini_required(self.ROOT_SAMPLE_NAME)
        self.add_ini_discovered(ini.SAMPLE_NAME_WG_N)
        self.add_ini_discovered(ini.SAMPLE_NAME_WG_T)
        self.add_ini_discovered(ini.SAMPLE_NAME_WT_T)

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
