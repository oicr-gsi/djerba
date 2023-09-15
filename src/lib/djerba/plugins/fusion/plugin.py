"""
Plugin to generate the Fusions report section
"""

import csv
import logging
import os
import re
from djerba.plugins.base import plugin_base
from djerba.plugins.fusion.tools import fusion_reader
from djerba.util.html import html_builder as hb
from djerba.util.logger import logger
from djerba.util.oncokb.annotator import oncokb_annotator
from djerba.util.oncokb.cache import oncokb_cache_params
from djerba.util.render_mako import mako_renderer
from djerba.util.subprocess_runner import subprocess_runner
import djerba.core.constants as core_constants
import djerba.util.oncokb.level_tools as oncokb_levels
import djerba.util.oncokb.constants as oncokb

class main(plugin_base):

    PRIORITY = 400
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'fusion_template.html'

    # INI config keys
    MAVIS_PATH = 'mavis path'
    ENTREZ_CONVERSION_PATH = 'entrez conv path'
    MIN_FUSION_READS = 'minimum fusion reads'
    ONCOTREE_CODE = 'oncotree code'
    ONCOKB_CACHE = 'oncokb cache'
    APPLY_CACHE = 'apply cache'
    UPDATE_CACHE = 'update cache'

    # JSON results keys
    TOTAL_VARIANTS = "Total variants"
    CLINICALLY_RELEVANT_VARIANTS = "Clinically relevant variants"
    BODY = 'body'
    FRAME = 'frame'
    GENE = 'gene'
    GENE_URL = 'gene URL'
    CHROMOSOME = 'chromosome'
    FUSION = 'fusion'
    MUTATION_EFFECT = 'mutation effect'
    # ONCOKB is from core constants

    # other constants
    ENTRCON_NAME = 'entrez_conversion.txt'

    def annotate_fusion_files(self, config_wrapper):
        # annotate from OncoKB
        cache_params = oncokb_cache_params(
            config_wrapper.get_my_string(self.ONCOKB_CACHE),
            config_wrapper.get_my_boolean(self.APPLY_CACHE),
            config_wrapper.get_my_boolean(self.UPDATE_CACHE),
            log_level=self.log_level,
            log_path=self.log_path
        )
        self.logger.debug("OncoKB cache params: {0}".format(cache_params))
        annotator = oncokb_annotator(
            config_wrapper.get_my_string(core_constants.TUMOUR_ID),
            config_wrapper.get_my_string(self.ONCOTREE_CODE),
            self.workspace.get_work_dir(), # output dir
            self.workspace.get_work_dir(), # temporary dir -- same as output
            cache_params,
            self.log_level,
            self.log_path
        )
        # TODO check if fusions are non empty
        annotator.annotate_fusion()

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        # TODO populate the oncotree code
        data_dir = os.environ.get(core_constants.DJERBA_DATA_DIR_VAR)
        if wrapper.my_param_is_null(self.ENTREZ_CONVERSION_PATH):
            enscon_path = os.path.join(data_dir, self.ENTRCON_NAME)
            wrapper.set_my_param(self.ENTREZ_CONVERSION_PATH, enscon_path)
        if wrapper.my_param_is_null(self.MAVIS_PATH):
            path_info = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
            mavis_path = path_info.get('mavis')
            if mavis_path == None:
                msg = 'Cannot find Mavis path for fusion input'
                self.logger.error(msg)
                raise RuntimeError(msg)
            wrapper.set_my_param(self.MAVIS_PATH, mavis_path)
        if wrapper.my_param_is_null(core_constants.TUMOUR_ID):
            sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            tumour_id = sample_info.get(core_constants.TUMOUR_ID)
            wrapper.set_my_param(core_constants.TUMOUR_ID, tumour_id)
        return wrapper.get_config()

    def cytoband_lookup(self):
        data_dir = os.environ.get(core_constants.DJERBA_DATA_DIR_VAR)
        cytoband_path = os.path.join(data_dir, 'cytoBand.txt')
        cytobands = {}
        with open(cytoband_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                cytobands[row['Hugo_Symbol']] = row['Chromosome']
        return cytobands

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        self.process_fusion_files(wrapper)
        cytobands = self.cytoband_lookup()
        fus_reader = fusion_reader(
            self.workspace.get_work_dir(), self.log_level, self.log_path
        )
        total_fusion_genes = fus_reader.get_total_fusion_genes()
        gene_pair_fusions = fus_reader.get_fusions()
        if gene_pair_fusions is not None:
            # table has 2 rows for each oncogenic fusion
            rows = []
            for fusion in gene_pair_fusions:
                oncokb_level = fusion.get_oncokb_level()
                for gene in fusion.get_genes():
                    row =  {
                        self.GENE: gene,
                        self.GENE_URL: hb.build_gene_url(gene),
                        self.CHROMOSOME: cytobands.get(gene),
                        self.FRAME: fusion.get_frame(),
                        self.FUSION: fusion.get_fusion_id_new(),
                        self.MUTATION_EFFECT: fusion.get_mutation_effect(),
                        core_constants.ONCOKB: oncokb_level
                    }
                    rows.append(row)
            # rows are already sorted by the fusion reader
            rows = list(filter(oncokb_levels.oncokb_filter, rows))
            distinct_oncogenic_genes = len(set([row.get(self.GENE) for row in rows]))
            results = {
                self.TOTAL_VARIANTS: total_fusion_genes,
                self.CLINICALLY_RELEVANT_VARIANTS: distinct_oncogenic_genes,
                self.BODY: rows
            }
        else:
            results = {
                self.TOTAL_VARIANTS: 0,
                self.CLINICALLY_RELEVANT_VARIANTS: 0,
                self.BODY: []
            }
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS] = results
        return data

    def process_fusion_files(self, config_wrapper):
        """
        Preprocess fusion inputs and run R scripts; write outputs to the workspace
        Inputs assumed to be in Mavis .tab format; .zip format is no longer in use
        """
        mavis_path = config_wrapper.get_my_string(self.MAVIS_PATH)
        tumour_id = config_wrapper.get_my_string(core_constants.TUMOUR_ID)
        entrez_conv_path = config_wrapper.get_my_string(self.ENTREZ_CONVERSION_PATH)
        min_reads = config_wrapper.get_my_int(self.MIN_FUSION_READS)
        fus_path = self.workspace.abs_path('fus.txt')
        self.logger.info("Processing fusion results from "+mavis_path)
        # prepend a column with the tumour ID to the Mavis .tab output
        with open(mavis_path, 'rt') as in_file, open(fus_path, 'wt') as out_file:
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            in_header = True
            for row in reader:
                if in_header:
                    value = 'Sample'
                    in_header = False
                else:
                    value = tumour_id
                new_row = [value] + row
                writer.writerow(new_row)
        # run the R script
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.join(plugin_dir, 'fusions.R')
        cmd = [
            'Rscript', script_path,
            '--entcon', entrez_conv_path,
            '--fusfile', fus_path,
            '--minfusionreads', min_reads,
            '--outdir', os.path.abspath(self.workspace.get_work_dir())
        ]
        subprocess_runner(self.log_level, self.log_path).run([str(x) for x in cmd])
        self.annotate_fusion_files(config_wrapper)
        self.logger.info("Finished writing fusion files")

    def specify_params(self):
        self.add_ini_discovered(self.ENTREZ_CONVERSION_PATH)
        self.add_ini_discovered(self.MAVIS_PATH)
        self.add_ini_discovered(core_constants.TUMOUR_ID)
        self.add_ini_discovered(self.ONCOTREE_CODE)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(self.MIN_FUSION_READS, 20)
        self.set_ini_default(self.APPLY_CACHE, False)
        self.set_ini_default(self.UPDATE_CACHE, False)
        cache_default = '/.mounts/labs/CGI/gsi/tools/djerba/oncokb_cache/scratch'
        self.set_ini_default(self.ONCOKB_CACHE, cache_default)
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
