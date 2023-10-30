"""Helper to write expression data, for use by SNV/indel and CNV plugins"""

import csv
import gzip
import logging
import os
import djerba.util.constants as constants
import djerba.util.ini_fields as ini
import djerba.core.constants as core_constants
from djerba.helpers.provenance_helper.helper import main as fpr_helper
from djerba.helpers.base import helper_base
from djerba.util.environment import directory_finder
from djerba.util.provenance_reader import provenance_reader, sample_name_container
from djerba.util.subprocess_runner import subprocess_runner

class main(helper_base):

    ENSCON_KEY = 'enscon'
    GENE_LIST_KEY = 'gene_list'
    GEP_REFERENCE_KEY = 'gep_reference'
    RSEM_GENES_RESULTS_KEY = 'rsem_genes_results'
    TCGA_CODE_KEY = 'tcga_code'
    TCGA_DATA_KEY = 'tcga_data'
    TCGA_EXPR_PCT_TEXT = 'data_expression_percentile_tcga.txt'
    TCGA_EXPR_PCT_JSON = 'data_expression_percentile_tcga.json'

    # 0-based index for GEP results file
    GENE_ID = 0
    FPKM = 6

    FPR_NAME = 'provenance_helper'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        data_dir = directory_finder(self.log_level, self.log_path).get_data_dir()
        # get donor/project/tumour id and sample names from provenance helper JSON
        sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
        donor = sample_info[fpr_helper.ROOT_SAMPLE_NAME]
        project = sample_info[fpr_helper.STUDY_TITLE]
        sample_wg_n = sample_info[ini.SAMPLE_NAME_WG_N]
        sample_wg_t = sample_info[ini.SAMPLE_NAME_WG_T]
        sample_wt_t = sample_info[ini.SAMPLE_NAME_WT_T]
        if wrapper.my_param_is_null(core_constants.TUMOUR_ID):
            tumour_id = sample_info[core_constants.TUMOUR_ID]
            wrapper.set_my_param(core_constants.TUMOUR_ID, tumour_id)
        self.update_wrapper_if_null(
            wrapper,
            'input_params.json',
            self.TCGA_CODE_KEY,
            'tcgacode'
        )
        if wrapper.my_param_is_null(self.GEP_REFERENCE_KEY):
            ref_path = os.path.join(data_dir, 'results', 'gep_reference.txt.gz')
            wrapper.set_my_param(self.GEP_REFERENCE_KEY, ref_path)
        if wrapper.my_param_is_null(self.ENSCON_KEY):
            ref_path = os.path.join(data_dir, 'ensemble_conversion_hg38.txt')
            wrapper.set_my_param(self.ENSCON_KEY, ref_path)
        if wrapper.my_param_is_null(self.GENE_LIST_KEY):
            ref_path = os.path.join(data_dir, 'targeted_genelist.txt')
            wrapper.set_my_param(self.GENE_LIST_KEY, ref_path)
        # set up and run the provenance reader
        samples = sample_name_container()
        samples.set_and_validate(sample_wg_n, sample_wg_t, sample_wt_t)
        fpr_path = self.workspace.abs_path(fpr_helper.PROVENANCE_OUTPUT)
        reader = provenance_reader(fpr_path, project, donor, samples,
                                   log_level=self.log_level, log_path=self.log_path)
        if wrapper.my_param_is_null(self.RSEM_GENES_RESULTS_KEY):
            rsem_genes_results = reader.parse_gep_path()
            wrapper.set_my_param(self.RSEM_GENES_RESULTS_KEY, rsem_genes_results)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        results = wrapper.get_my_string(self.RSEM_GENES_RESULTS_KEY)
        gep_reference = wrapper.get_my_string(self.GEP_REFERENCE_KEY)
        tumour_id = wrapper.get_my_string(core_constants.TUMOUR_ID)
        gep_abs_path = self.preprocess_gep(results, gep_reference, tumour_id)
        # Run the R script with output to the workspace
        cmd = [
            'Rscript',
            os.path.join(self.get_module_dir(), 'find_expression.R'),
            '--enscon', wrapper.get_my_string(self.ENSCON_KEY),
            '--genelist', wrapper.get_my_string(self.GENE_LIST_KEY),
            '--gepfile', gep_abs_path,
            '--outdir', self.workspace.get_work_dir(),
            '--tcgadata', wrapper.get_my_string(self.TCGA_DATA_KEY),
            '--tcgacode', wrapper.get_my_string(self.TCGA_CODE_KEY)
        ]
        self.logger.debug("Rscript command: "+" ".join(cmd))
        subprocess_runner(self.log_level, self.log_path).run(cmd)
        self.write_tcga_json()

    def preprocess_gep(self, gep_path, gep_reference, tumour_id):
        """
        Apply preprocessing to a GEP file; write results to tmp_dir
        CGI-Tools constructs the GEP file from scratch, but only one column actually varies
        As a shortcut, we insert the first column into a ready-made file
        TODO This is a legacy CGI-Tools method, is there a cleaner way to do it?
        TODO Should GEP_REFERENCE (list of past GEP results) be updated on a regular basis?
        """
        # read the gene id and FPKM metric from the GEP file for this report
        fkpm = {}
        with open(gep_path) as gep_file:
            reader = csv.reader(gep_file, delimiter="\t")
            for row in reader:
                try:
                    fkpm[row[self.GENE_ID]] = row[self.FPKM]
                except IndexError as err:
                    msg = "Incorrect number of columns in GEP row: '{0}'".format(row)+\
                          "read from '{0}'".format(gep_path)
                    self.logger.error(msg)
                    raise RuntimeError(msg) from err
        # insert as the second column in the generic GEP file
        ref_path = gep_reference
        out_file_name = 'gep.txt'
        with \
             gzip.open(ref_path, 'rt', encoding=constants.TEXT_ENCODING) as in_file, \
             self.workspace.open_file(out_file_name, 'wt') as out_file:
            # preprocess the GEP file
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    row.insert(1, tumour_id)
                    first = False
                else:
                    gene_id = row[0]
                    try:
                        row.insert(1, fkpm[gene_id])
                    except KeyError as err:
                        msg = 'Reference gene ID {0} from {1} '.format(gene_id, ref_path) +\
                            'not found in gep results path {0}'.format(gep_path)
                        self.logger.warn(msg)
                        row.insert(1, '0.0')
                writer.writerow(row)
        return self.workspace.abs_path(out_file_name)

    def specify_params(self):
        defaults = {
            core_constants.DEPENDS_CONFIGURE: 'provenance_helper',
            self.TCGA_DATA_KEY: '/.mounts/labs/CGI/gsi/tools/RODiC/data',
            self.GEP_REFERENCE_KEY: '/.mounts/labs/CGI/gsi/tools/djerba/gep_reference.txt.gz'
        }
        for key in defaults.keys():
            self.set_ini_default(key, defaults[key])
        self.add_ini_discovered(self.ENSCON_KEY)
        self.add_ini_discovered(self.GENE_LIST_KEY)
        self.add_ini_discovered(self.RSEM_GENES_RESULTS_KEY)
        self.add_ini_discovered(self.TCGA_CODE_KEY) # use PAAD for testing
        self.add_ini_discovered(core_constants.TUMOUR_ID)

    def write_tcga_json(self):
        """Write TCGA expression percentiles in JSON format, for use by other plugins"""
        expr = {}
        with self.workspace.open_file(self.TCGA_EXPR_PCT_TEXT) as input_file:
            for row in csv.reader(input_file, delimiter="\t"):
                if row[0]=='Hugo_Symbol':
                    continue
                gene = row[0]
                try:
                    metric = float(row[1])
                except ValueError as err:
                    msg = 'Cannot convert expression value "{0}" to float, '.format(row[1])+\
                          '; using 0 as fallback value: {0}'.format(err)
                    self.logger.warning(msg)
                    metric = 0.0
                expr[gene] = metric
        self.workspace.write_json(self.TCGA_EXPR_PCT_JSON, expr)
