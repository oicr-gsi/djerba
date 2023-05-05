"""Helper to write expression data, for use by SNV/indel and CNV plugins"""

import csv
import gzip
import logging
import os
import djerba.util.constants as constants
import djerba.core.constants as core_constants
from djerba.helpers.provenance_helper.helper import main as fpr_helper
from djerba.helpers.base import helper_base
from djerba.util.provenance_reader import provenance_reader, sample_name_container
from djerba.util.subprocess_runner import subprocess_runner

class main(helper_base):

    ENSCON_KEY = 'enscon'
    GENE_LIST_KEY = 'gene_list'
    GEP_REFERENCE_KEY = 'gep_reference'
    RSEM_GENES_RESULTS_KEY = 'rsem_genes_results'
    TCGA_DATA_KEY = 'tgca_data'
    TCGA_CODE_KEY = 'tgca_code'
    TUMOUR_ID = 'tumour_id' # TODO put in core params

    # 0-based index for GEP results file
    GENE_ID = 0
    FPKM = 6
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        defaults = {
            self.ENSCON_KEY: '${DJERBA_DATA_DIR}/ensemble_conversion_hg38.txt',
            self.GENE_LIST_KEY: '${DJERBA_DATA_DIR}/targeted_genelist.txt',
            self.GEP_REFERENCE_KEY: '/home/ibancarz/workspace/djerba/test/20230505_02/gep_reference.txt.gz', # TODO FIXME
            self.RSEM_GENES_RESULTS_KEY: 'NULL',
            self.TCGA_DATA_KEY: '/.mounts/labs/CGI/gsi/tools/RODiC/data',
            self.TCGA_CODE_KEY: 'NULL'
        }
        self.set_all_ini_defaults(defaults)
        self.add_ini_required(self.TCGA_CODE_KEY)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.apply_my_env_templates()
        fpr_path = self.workspace.abs_path(fpr_helper.PROVENANCE_OUTPUT)
        donor = wrapper.get_core_string(core_constants.DONOR)
        project = wrapper.get_core_string(core_constants.PROJECT)
        if wrapper.get_my_string(self.TCGA_CODE_KEY) == 'NULL': # TODO implement is_null()
            wrapper.set_my_param(self.TCGA_CODE_KEY, project)
        samples = sample_name_container() # empty container; TODO sample names in INI
        reader = provenance_reader(fpr_path, project, donor, samples)
        rsem_genes_results = reader.parse_gep_path()
        wrapper.set_my_param(self.RSEM_GENES_RESULTS_KEY, rsem_genes_results)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        results = wrapper.get_my_string(self.RSEM_GENES_RESULTS_KEY)
        gep_reference = wrapper.get_my_string(self.GEP_REFERENCE_KEY)
        tumour_id = wrapper.get_core_string(self.TUMOUR_ID)
        gep_abs_path = self.preprocess_gep(results, gep_reference, tumour_id)
        # Run the R script with output to the workspace
        cmd = [
            'Rscript',
            os.path.join(self.get_module_dir(), 'find_expression.R'),
            '--enscon ', wrapper.get_my_string(self.ENSCON_KEY),
            '--genelist', wrapper.get_my_string(self.GENE_LIST_KEY),
            '--gepfile', gep_abs_path,
            '--outdir', self.workspace.get_work_dir(),
            '--tcgadata', wrapper.get_my_string(self.TCGA_DATA_KEY),
            '--tcgacode', wrapper.get_my_string(self.TCGA_CODE_KEY)
        ]
        self.logger.debug("Rscript command: "+" ".join(cmd))
        #subprocess_runner(self.log_level, self.log_path).run(cmd)

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


