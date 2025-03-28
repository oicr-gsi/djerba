import os
import csv
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 1000
    PLUGIN_VERSION = '0.1.0'
    TEMPLATE_NAME = 'hla_template.html'

    HLA_FILE_PATH= 't1k_file'
    HLA_WORKFLOW = 't1k'

    # Constants for TSV columns
    GENE_NAME = 'Gene name'
    ZYGOSITY = 'Zygosity'
    ALLELE = 'Allele'
    #ABUNDANCE = 'Abundance'
    #QUALITY = 'Quality'
    BODY = 'Body'

    def specify_params(self):

        self.add_ini_discovered(self.HLA_FILE_PATH)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)


    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            self.HLA_FILE_PATH,
            self.HLA_WORKFLOW)

        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        tsv_path = config[self.identifier][self.HLA_FILE_PATH]

        data = {
            'plugin_name': 'Germline HLA Analysis',
            'version': self.PLUGIN_VERSION,
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {},
            'results': self.build_hla_table(work_dir, tsv_path)
        }
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)

    def build_hla_table(self, work_dir, tsv_path):
        # T1K HLA output also includes:
        # - "Abundance": Proportion of reads supporting an allele.
        # - "Quality": Confidence score based on depth, base quality, and alignment.
        # Uncomment these variables if you want them included in the table.

        if tsv_path is None:
            self.logger.warning("HLA Analysis: 't1k_file' is missing or set to None. No HLA data will be displayed.")
            return []

        tsv_full_path = os.path.join(work_dir, tsv_path)

        if not os.path.exists(tsv_full_path):
            self.logger.warning(
                f"HLA Analysis: Expected TSV file not found: {tsv_full_path}. No HLA data will be displayed.")
            return []

        if os.path.getsize(tsv_full_path) == 0:
            self.logger.warning(f"HLA Analysis: TSV file {tsv_full_path} is empty. No HLA data will be displayed.")
            return []

        rows = []
        with open(tsv_full_path) as data_file:
            for input_row in csv.reader(data_file, delimiter="\t"):
                gene_name = input_row[0]

                # Only consider HLA-A, HLA-B, and HLA-C
                if gene_name not in ['HLA-A', 'HLA-B', 'HLA-C']:
                    continue

                zygosity = 'Homozygous' if input_row[1] == '1' else 'Heterozygous'
                allele1 = input_row[2]
                #abundance1 = input_row[3]
                #quality1 = input_row[4]
                allele2 = input_row[5]
                #abundance2 = input_row[6]
                #quality2 = input_row[7]

                if zygosity == 'Homozygous':
                    rows.append({
                        self.GENE_NAME: gene_name,
                        self.ZYGOSITY: zygosity,
                        self.ALLELE: allele1,
                        #self.ABUNDANCE: abundance1,
                        #self.QUALITY: quality1
                    })
                else:
                    rows.append({
                        self.GENE_NAME: gene_name,
                        self.ZYGOSITY: zygosity,
                        self.ALLELE: allele1,
                        #self.ABUNDANCE: abundance1,
                        #self.QUALITY: quality1
                    })
                    rows.append({
                        self.GENE_NAME: '',
                        self.ZYGOSITY: '',
                        self.ALLELE: allele2,
                        #self.ABUNDANCE: abundance2,
                        #self.QUALITY: quality2
                    })

        data = {
            self.BODY: rows
        }

        return data

