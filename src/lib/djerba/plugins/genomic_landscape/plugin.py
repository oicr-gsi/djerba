"""
Plugin to generate the Genomic Landscape report section
"""

import logging
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 300
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'genomic_landscape_template.html'

    # input keys
    MAF_PATH = 'maf path'
    
    # results keys
    COHORT = 'cohort'
    COHORT_PERCENTILE = 'cohort percentile'
    CTDNA_CANDIDATES = 'ctDNA candidates'
    CTDNA_MIN = 'ctDNA minimum'
    CTDNA_STATUS = 'ctDNA status'
    MSI_CALL = 'MSI call'
    MSI_OK = 'MSI OK' # boolean
    MSI_PLOT = 'MSI plot'
    MSI_STATUS = 'MSI status'
    PAN_CANCER_PERCENTILE = 'pan cancer percentile'
    TMB = 'TMB'
    TMB_CALL = 'TMB call'
    TMB_CLASS = 'TMB class'
    TMB_PLOT = 'TMB plot'
    TOTAL_MUTATIONS = 'total mutations'

    # constants
    COHORT_DEFAULT = 'COMPASS'
    CTDNA_MIN_DEFAULT = 4000
    TMB_THRESHOLD = 10

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        

        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        # TODO find metric values and make plots here
        # TODO check MSI status. Get purity from sample information plugin
        # TODO preprocess MSI file as in r_script_wrapper.py
        # TODO preprocess MAF files? or do in a helper?
        # TODO process MAF files with code from singlesample.r script
        # TODO run biomarker R script to generate TMB and MSI plots
        results = {
            self.COHORT: wrapper.get_my_string(self.COHORT),
            self.CTDNA_MIN: wrapper.get_my_int(self.CTDNA_MIN)
        }
        data[core_constants.RESULTS] = results
        return data

    def preprocess_maf(self, maf_path, tumour_id, oncotree_code, cache_params):
        """Apply preprocessing and annotation to a MAF file; write results to tmp_dir"""
        tmp_name = 'tmp_maf.tsv'
        self.logger.info("Preprocessing MAF input")
        # find the relevant indices on-the-fly from MAF column headers
        # use this instead of csv.DictReader to preserve the rows for output
        with \
             gzip.open(maf_path, 'rt', encoding=core_constants.TEXT_ENCODING) as in_file, \
             self.workspace.open_file(tmp_name, 'wt') as tmp_file:
            # preprocess the MAF file
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(tmp_file, delimiter="\t")
            in_header = True
            total = 0
            kept = 0
            for row in reader:
                if in_header:
                    if re.match('#version', row[0]):
                        # do not write the version header
                        continue
                    else:
                        # write the column headers without change
                        writer.writerow(row)
                        indices = self._read_maf_indices(row)
                        in_header = False
                else:
                    total += 1
                    if self._maf_body_row_ok(row, indices):
                        # filter rows in the MAF body and update the tumour_id
                        row[indices.get(self.TUMOUR_SAMPLE_BARCODE)] = self.tumour_id
                        writer.writerow(row)
                        kept += 1
        self.logger.info("Kept {0} of {1} MAF data rows".format(kept, total))
        # apply annotation to tempfile and return final output
        out_path = oncokb_annotator(
            tumour_id,
            oncotree_code,
            self.workspace.get_work_dir(), # working directory
            self.workspace.get_work_dir(), # temporary directory -- can be the same
            cache_params,
            self.log_level,
            self.log_path
        ).annotate_maf(self.workspace.abs_path(tmp_name))
        return out_path

    def specify_params(self):
        self.set_ini_default(self.COHORT, self.COHORT_DEFAULT)
        self.set_ini_default(self.CTDNA_MIN, self.CTDNA_MIN_DEFAULT)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
