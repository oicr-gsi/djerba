import os
import csv
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '0.1.0'
    TEMPLATE_NAME = 'hla_template.html'

    T1K_FILE_PATH= 'tsv_file'

    # Constants for TSV columns
    GENE_NAME = 'Gene name'
    ZYGOSITY = 'Zygosity'
    ALLELE = 'Allele'
    ABUNDANCE = 'Abundance'
    QUALITY = 'Quality'

    def specify_params(self):

        self.add_ini_discovered(self.T1K_FILE_PATH)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)


    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            self.T1K_FILE_PATH,
            fallback=os.path.realpath("/.mounts/labs/CGI/scratch/ohamza/HLA_plugin/T1K_output_files/OCT_010434_Ly_R_WG_t1k_hla_genotype.tsv"))

        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        tsv_path = config[self.identifier][self.T1K_FILE_PATH]

        data = {
            'plugin_name': 'HLA Analysis',
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
        rows = []
        with open(os.path.join(work_dir, tsv_path)) as data_file:
            for input_row in csv.reader(data_file, delimiter="\t"):
                gene_name = input_row[0]
                zygosity = 'Homozygous' if input_row[1] == '1' else 'Heterozygous'
                allele1 = input_row[2]
                abundance1 = input_row[3]
                quality1 = input_row[4]
                allele2 = input_row[5]
                abundance2 = input_row[6]
                quality2 = input_row[7]

                if zygosity == 'homozygous':
                    rows.append({
                        self.GENE_NAME: gene_name,
                        self.ZYGOSITY: zygosity,
                        self.ALLELE: allele1,
                        self.ABUNDANCE: abundance1,
                        self.QUALITY: quality1
                    })
                else:
                    rows.append({
                        self.GENE_NAME: gene_name,
                        self.ZYGOSITY: zygosity,
                        self.ALLELE: allele1,
                        self.ABUNDANCE: abundance1,
                        self.QUALITY: quality1
                    })
                    rows.append({
                        self.GENE_NAME: '',
                        self.ZYGOSITY: '',
                        self.ALLELE: allele2,
                        self.ABUNDANCE: abundance2,
                        self.QUALITY: quality2
                    })
        return rows
