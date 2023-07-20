"""Helper for writing a subset of file provenance to the shared workspace"""

import csv
import gzip
import logging
import djerba.util.ini_fields as ini
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base
from djerba.util.provenance_reader import provenance_reader, sample_name_container, \
    InvalidConfigurationError

class main(helper_base):

    PROVENANCE_INPUT = 'provenance_input_path'
    STUDY_TITLE = 'study_title'
    ROOT_SAMPLE_NAME = 'root_sample_name'
    PROVENANCE_OUTPUT = 'provenance_subset.tsv.gz'
    PRIORITY = 50

    # No automated configuration; use placeholder method of parent class
    # Needs study title, root sample name, provenance path; configured manually (for now)
    # Optionally, provide WG-N/WG-T/WT-T sample names in INI

    def extract(self, config):
        self.validate_full_config(config)
        wrapper = self.get_config_wrapper(config)
        provenance_path = wrapper.get_my_string(self.PROVENANCE_INPUT)
        study = wrapper.get_my_string(self.STUDY_TITLE)
        donor = wrapper.get_my_string(self.ROOT_SAMPLE_NAME)
        self.logger.info('Started reading file provenance from {0}'.format(provenance_path))
        total = 0
        with gzip.open(provenance_path, 'rt') as in_file, \
             self.workspace.open_gzip_file(self.PROVENANCE_OUTPUT, write=True) as out_file:
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            for row in reader:
                total += 1
                if total % 100000 == 0:
                    self.logger.debug("Read {0} rows".format(total))
                if row[index.STUDY_TITLE] == study and row[index.ROOT_SAMPLE_NAME] == donor:
                    writer.writerow(row)
        self.logger.debug('Done; read {0} rows'.format(total))
        self.logger.info('Finished reading file provenance from {0}'.format(provenance_path))
        # parse the file provenance subset and write sample_info.json to the workspace
        samples = sample_name_container()
        if wrapper.has_my_param(ini.SAMPLE_NAME_WG_N):
            samples.set_wg_n(wrapper.get_my_param(key))
        if wrapper.has_my_param(ini.SAMPLE_NAME_WG_T):
            samples.set_wg_t(wrapper.get_my_param(key))
        if wrapper.has_my_param(ini.SAMPLE_NAME_WT_T):
            samples.set_wt_t(wrapper.get_my_param(key))
        if samples.is_valid():
            self.logger.debug("Configured sample names are valid")
        else:
            msg = "Invalid sample name configuration: {0}.".format(samples)
            msg = msg + " Must either be empty, or have at least WG tumour/normal names"
            self.logger.error(msg)
            raise InvalidConfigurationError(msg)
        subset_path = self.workspace.abs_path(self.PROVENANCE_OUTPUT)
        reader = provenance_reader(subset_path, study, donor, samples)
        names = reader.get_sample_names()

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.add_ini_required(self.PROVENANCE_INPUT)
        self.set_priority_defaults(self.PRIORITY)
