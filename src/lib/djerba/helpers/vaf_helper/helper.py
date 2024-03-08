import csv
import gzip
import logging
from djerba.helpers.base import helper_base
from djerba.util.validator import path_validator

class main(helper_base):

    HUGO_SYMBOL = 'Hugo_Symbol'
    PRIORITY = 10
    MAF_PATH = 'maf_path'
    OUTPUT_FILENAME = 'vaf_by_gene.json'

    def specify_params(self):
        self.logger.debug("Specifying params for input params helper")
        self.set_priority_defaults(self.PRIORITY)
        self.add_ini_required(self.MAF_PATH) # TODO discover from file provenance

    def configure(self, config):
        config = self.apply_defaults(config)        
        return config

    def get_tumour_vaf(self, row):
        msg = None
        try:
            vaf = float(row['t_alt_count'])/float(row['t_depth'])
        except KeyError as err:
            msg = "Cannot find VAF: Incorrectly formatted MAF row? {0}".format(row)
        except ZeroDivisionError as err:
            msg = "Cannot find VAF: Zero depth in MAF row {0}".format(row)
        if msg:
            self.logger.error(msg)
            raise RuntimeError(msg) from err
        return vaf

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        maf_path = wrapper.get_my_string(self.MAF_PATH)
        path_validator(self.log_level, self.log_path).validate_input_file(maf_path)
        vaf_by_gene = {}
        with gzip.open(maf_path, 'rt') as maf_file:
            reader = csv.DictReader(filter(lambda row: row[0]!='#', maf_file),delimiter="\t")
            for row in reader:
                gene = row[self.HUGO_SYMBOL]
                vaf = self.get_tumour_vaf(row)
                vaf_by_gene[gene] = vaf
        self.workspace.write_json(self.OUTPUT_FILENAME, vaf_by_gene)
