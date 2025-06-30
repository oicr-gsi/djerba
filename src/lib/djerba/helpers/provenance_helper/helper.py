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
    STUDY_TITLE = 'project'
    ROOT_SAMPLE_NAME = 'donor'
    ASSAY = 'assay'
    PROVENANCE_OUTPUT = 'provenance_subset.tsv.gz'
    PRIORITY = 50
    SAMPLE_NAME_KEYS = [
        ini.SAMPLE_NAME_WG_N,
        ini.SAMPLE_NAME_WG_T,
        ini.SAMPLE_NAME_WT_T
    ]
    TAR = 'TAR'

    # identifiers for bam/bai files
    WG_N_BAM = 'whole genome normal bam'
    WG_N_IDX = 'whole genome normal bam index'
    WG_T_BAM = 'whole genome tumour bam'
    WG_T_IDX = 'whole genome tumour bam index'
    WT_T_BAM = 'whole transcriptome tumour bam'
    WT_T_IDX = 'whole transcriptome tumour bam index'

    # identifiers for tar files which come from the same workflow
    WF_CONSENSUS_TUMOUR = 'consensusCruncher_tumour'
    WF_CONSENSUS_NORMAL = 'consensusCruncher_normal'
    WF_MAF_TUMOUR = 'maf_tumour'
    WF_MAF_NORMAL = 'maf_normal'
    WF_ICHOR_JSON = 'metrics_json'
    WF_ICHOR_SEG = 'seg'
    WF_ICHOR_PLOTS = 'plots'

    VERSION = '1.0.0'

    def configure(self, config):
        """
        Writes a subset of provenance, and informative JSON files, to the workspace
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        provenance_path = wrapper.get_my_string(self.PROVENANCE_INPUT_KEY)
        input_data = self.workspace.read_maybe_input_params()
        if input_data == None:
            msg = "Input params JSON does not exist. Parameters must be set manually."
            self.logger.warning(msg)
        # Get the study/sample parameters
        for key in [self.STUDY_TITLE, self.ROOT_SAMPLE_NAME, self.ASSAY]:
            if wrapper.my_param_is_null(key):
                if input_data == None:
                    msg = "Cannot resolve INI parameter '{0}'; ".format(key)+\
                        "input params JSON not available, and no manual INI value was given"
                    self.logger.error(msg)
                    raise DjerbaProvenanceError(msg)
                else:
                    wrapper.set_my_param(key, input_data[key])
        study = wrapper.get_my_string(self.STUDY_TITLE)
        donor = wrapper.get_my_string(self.ROOT_SAMPLE_NAME)
        assay = wrapper.get_my_string(self.ASSAY)
        if self.workspace.has_file(self.PROVENANCE_OUTPUT):
            self.logger.debug("Provenance subset cache exists, will not overwrite")
        else:
            self.logger.info("Writing provenance subset cache to workspace")
            self.write_provenance_subset(study, donor, provenance_path)
        self.print_illumina_instrument_version()

        samples = self.get_sample_name_container(wrapper, assay)
        sample_info, path_info = self.read_provenance(study, donor, assay, samples)
        self.write_path_info(path_info)
        keys = [core_constants.TUMOUR_ID, core_constants.NORMAL_ID]
        keys.extend(self.SAMPLE_NAME_KEYS)
        for key in keys:
            value = sample_info.get(key)
            if wrapper.my_param_is_null(key):
                if value == None:
                    msg = "No value found for parameter '{0}' ".format(key)+\
                        "in sample info or user config; need to add to config INI?"
                    self.logger.error(msg)
                    raise DjerbaProvenanceError(msg)
                else:
                    wrapper.set_my_param(key, value)
            elif wrapper.my_param_is_not_null(key):
                user_value = wrapper.get_my_string(key)
                msg = "Overwriting found value '{0}' for '{1}' in sample info with user-defined value '{2}'".format(value, key, user_value)
                self.logger.warning(msg)
                sample_info[key] = user_value
 
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
        assay = wrapper.get_my_string(self.ASSAY)
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
            samples = self.get_sample_name_container(wrapper, assay)
            sample_info, path_info = self.read_provenance(study, donor, assay, samples)
            if not self.workspace.has_file(core_constants.DEFAULT_SAMPLE_INFO):
                self.logger.debug('extract: writing sample info')
                self.write_sample_info(sample_info)
            if not self.workspace.has_file(core_constants.DEFAULT_PATH_INFO):
                self.logger.debug('extract: writing path info')
                self.write_path_info(path_info)

    def get_sample_name_container(self, config_wrapper, assay):
        """
        Populate a sample name container for input to the file provenance reader
        Allowed configurations:
        - All values null
        - All values specified
        - WG tumour/normal names specified, WT name null
        """
        samples = sample_name_container()
        count = 0
        if config_wrapper.my_param_is_not_null(ini.SAMPLE_NAME_WG_N):
            samples.set_wg_n(config_wrapper.get_my_string(ini.SAMPLE_NAME_WG_N))
            count += 1
        if config_wrapper.my_param_is_not_null(ini.SAMPLE_NAME_WG_T):
            samples.set_wg_t(config_wrapper.get_my_string(ini.SAMPLE_NAME_WG_T))
            count += 1
        if config_wrapper.my_param_is_not_null(ini.SAMPLE_NAME_WT_T):
            samples.set_wt_t(config_wrapper.get_my_string(ini.SAMPLE_NAME_WT_T))
            count += 1
        if samples.is_valid() and assay != self.TAR:
            self.logger.debug("Sample names from INI are valid: {0}".format(samples))
        elif assay == self.TAR:
            if count == 3:
                self.logger.debug("Sample names from INI for TAR assay are valid: {0}".format(samples))
            else:
                msg = "Invalid sample name configuration: {0}.".format(samples)
                msg = msg + " Must manually configure all 3 sample names for TAR assay samples."
                self.logger.error(msg)
                raise InvalidConfigurationError(msg)
        else:
            msg = "Invalid sample name configuration: {0}.".format(samples)
            msg = msg + " Must either be empty, or have at least WG tumour/normal names"
            self.logger.error(msg)
            raise InvalidConfigurationError(msg)
        return samples

    def print_illumina_instrument_version(self):
        """
        Starting 2025-07-03, the Illumina NovaSeq X Plus insturment version will change from v1.2 to v1.3.
        There will be a transition period in which the last of the v1.2 samples will be processed and newer samples will be done on the v1.3 instrument.
        After the transition period, some v1.2 reports might still need reprocessing.
        This function will print out the Illumina sequencing instrument version.
        Legend:
            LH00130 is v1.2
            LH00224 is v1.3
        """
        subset_path = self.workspace.abs_path(self.PROVENANCE_OUTPUT)
        with self.workspace.open_gzip_file(subset_path) as in_file:
                reader = csv.reader(in_file, delimiter="\t")
                xplus = False
                for row in reader:
                    if row[index.SEQUENCER_RUN_PLATFORM_NAME] == "Illumina_NovaSeq_X_Plus":
                        xplus = True
                        if "instrument_name=lh00130" in row[index.SEQUENCER_RUN_ATTRIBUTES].lower():
                            msg = "This case was sequenced on the Illumina NovaSeq X Plus sequencing instrument v1.2"
                            self.logger.warning(msg)
                            break
                        elif "instrument_name=lh00224" in row[index.SEQUENCER_RUN_ATTRIBUTES].lower():
                            msg = "This case was sequenced on the Illumina NovaSeq X Plus sequencing instrument v1.3"
                            self.logger.warning(msg)
                            break
                        else:
                            msg = "This case was sequenced on some other version of the Illumina NovaSeq X Plus sequencing instrument (neither v1.2 nor v1.3)."
                            self.logger.warning(msg)
                            break
                if not xplus:
                    msg = "This case was not sequenced on the Illumina NovaSeq X Plus. It may have been sequenced on the NovaSeq 6000."
                    self.logger.warning(msg)

    def read_provenance(self, study, donor, assay, samples):
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
            assay,
            samples,
            log_level=self.log_level,
            log_path=self.log_path
        )
        names = reader.get_sample_names()
        ids = reader.get_identifiers()
        
        sample_info = {
            self.STUDY_TITLE: study,
            self.ROOT_SAMPLE_NAME: donor,
            core_constants.PATIENT_STUDY_ID: ids.get(ini.PATIENT_ID_RAW),
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
            reader.WF_GRIDSS: reader.parse_gridss_path(),
            reader.WF_HRDETECT: reader.parse_hrdetect_path(),
            reader.WF_MAVIS: reader.parse_mavis_path(),
            reader.WF_MRDETECT: reader.parse_mrdetect_path(),
            reader.WF_MSISENSOR: reader.parse_msi_path(),
            reader.WF_MUTECT: reader.parse_mutect_path(),
            reader.WF_PURPLE: reader.parse_purple_zip_path(),
            reader.WF_RSEM: reader.parse_gep_path(),
            reader.WF_SEQUENZA: reader.parse_sequenza_path(),
            reader.WF_STAR: {
                self.WT_T_BAM: reader.parse_wt_bam_path(),
                self.WT_T_IDX: reader.parse_wt_index_path()
            },
            reader.WF_STARFUSION: reader.parse_starfusion_predictions_path(),
            reader.WF_VEP: reader.parse_maf_path(),
            reader.WF_VIRUS: reader.parse_virus_path(),
            reader.WF_IMMUNE: reader.parse_immune_path(),
            reader.WF_HLA: reader.parse_hla_path(),

            # TAR specific files:
            self.WF_CONSENSUS_TUMOUR: reader.parse_tar_metrics_tumour_path(),
            self.WF_CONSENSUS_NORMAL: reader.parse_tar_metrics_normal_path(),
            self.WF_MAF_TUMOUR: reader.parse_tar_maf_tumour_path(),
            self.WF_MAF_NORMAL: reader.parse_tar_maf_normal_path(),
            self.WF_ICHOR_JSON: reader.parse_tar_ichorcna_json_path(),
            self.WF_ICHOR_PLOTS: reader.parse_tar_ichorcna_plots_path(),
            self.WF_ICHOR_SEG: reader.parse_tar_ichorcna_seg_path()

        }
        return sample_info, path_info

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default(self.PROVENANCE_INPUT_KEY, self.DEFAULT_PROVENANCE_INPUT)
        self.add_ini_discovered(self.STUDY_TITLE)
        self.add_ini_discovered(self.ROOT_SAMPLE_NAME)
        self.add_ini_discovered(self.ASSAY)
        self.add_ini_discovered(ini.SAMPLE_NAME_WG_N)
        self.add_ini_discovered(ini.SAMPLE_NAME_WG_T)
        self.add_ini_discovered(ini.SAMPLE_NAME_WT_T)
        self.add_ini_discovered(core_constants.TUMOUR_ID)
        self.add_ini_discovered(core_constants.NORMAL_ID)

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

class DjerbaProvenanceError(Exception):
    pass
