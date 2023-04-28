"""Helper for writing a subset of file provenance to the shared workspace"""

import csv
import gzip
import djerba.util.ini_fields as ini
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base

class main(helper_base):

    PROVENANCE_INPUT = 'provenance_input_path'
    STUDY_TITLE = 'study_title'
    ROOT_SAMPLE_NAME = 'root_sample_name'
    PROVENANCE_OUTPUT = 'provenance_subset.tsv.gz'
    HELPER_NAME = 'provenance_helper'

    def configure(self, config):
        # No automated config
        # - uses study title and root sample name from core config
        # - provenance path must be configured manually (for now)
        return config

    def extract(self, config):
        provenance_path = config[self.HELPER_NAME][self.PROVENANCE_INPUT]
        study = config[ini.CORE][self.STUDY_TITLE]
        sample = config[ini.CORE][self.ROOT_SAMPLE_NAME]
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
                if row[index.STUDY_TITLE] == study and row[index.ROOT_SAMPLE_NAME] == sample:
                    writer.writerow(row)
        self.logger.info('Finished reading file provenance from {0}'.format(provenance_path))
