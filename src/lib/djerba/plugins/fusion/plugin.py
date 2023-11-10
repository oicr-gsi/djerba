"""
Plugin to generate the Fusions report section
"""

import csv
import logging
import os
import re
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.fusion.tools import fusion_reader
from djerba.plugins.wgts.tools import wgts_tools
from djerba.util.environment import directory_finder
from djerba.util.html import html_builder as hb
from djerba.util.logger import logger
from djerba.util.oncokb.annotator import annotator_factory
from djerba.util.oncokb.tools import gene_summary_reader
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.render_mako import mako_renderer
from djerba.util.subprocess_runner import subprocess_runner
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb

class main(plugin_base):

    PRIORITY = 900
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'fusion_template.html'

    # INI config keys
    MAVIS_PATH = 'mavis path'
    ONCOTREE_CODE = 'oncotree code'
    ENTREZ_CONVERSION_PATH = 'entrez conv path'
    MIN_FUSION_READS = 'minimum fusion reads'

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
        # TODO check if fusions are non empty
        factory = annotator_factory(self.log_level, self.log_path)
        work_dir = self.workspace.get_work_dir()
        factory.get_annotator(work_dir, config_wrapper).annotate_fusion()

    def build_treatment_entries(self, fusion, therapies):
        """Make an entry for the treatment options merger"""
        # TODO fix the treatment options merger to display 2 genes for fusions
        genes = fusion.get_genes()
        gene = genes[0]
        factory = tom_factory(self.log_level, self.log_path)
        entries = []
        for level in therapies.keys():
            entry = factory.get_json(
                tier=oncokb_levels.tier(level),
                level=level,
                treatments=therapies[level],
                gene=gene,
                alteration='Fusion',
                alteration_url=hb.build_fusion_url(genes, oncotree_code)
            )
            entries.append(entry)
        return entries

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        # find oncotree code and convert to lower case
        self.update_wrapper_if_null(
            wrapper,
            'input_params.json',
            self.ONCOTREE_CODE,
            'oncotree_code'
        )
        code_lc = wrapper.get_my_string(self.ONCOTREE_CODE).lower()
        wrapper.set_my_param(self.ONCOTREE_CODE, code_lc)
        # find other params
        data_dir = directory_finder(self.log_level, self.log_path).get_data_dir()
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

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        self.process_fusion_files(wrapper)
        fus_reader = fusion_reader(
            self.workspace.get_work_dir(), self.log_level, self.log_path
        )
        total_fusion_genes = fus_reader.get_total_fusion_genes()
        gene_pair_fusions = fus_reader.get_fusions()
        if gene_pair_fusions is not None:
            oncotree_code = wrapper.get_my_string(self.ONCOTREE_CODE)
            outputs = self.fusions_to_json(gene_pair_fusions, oncotree_code)
            [rows, gene_info, treatment_opts] = outputs
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
            gene_info = []
            treatment_opts = []
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS] = results
        data[core_constants.MERGE_INPUTS]['gene_information_merger'] = gene_info
        data[core_constants.MERGE_INPUTS]['treatment_options_merger'] = treatment_opts
        return data

    def fusions_to_json(self, gene_pair_fusions, oncotree_code):
        rows = []
        gene_info = []
        treatment_opts = []
        cytobands = wgts_tools(self.log_level, self.log_path).cytoband_lookup()
        summaries = gene_summary_reader(self.log_level, self.log_path)
        gene_info_factory = gim_factory(self.log_level, self.log_path)
        # table has 2 rows for each oncogenic fusion
        # retain fusions with sort order less than (ie. ahead of) 'Likely Oncogenic'
        maximum_order = oncokb_levels.oncokb_order('N2')
        for fusion in gene_pair_fusions:
            oncokb_order = oncokb_levels.oncokb_order(fusion.get_strongest_oncokb_level())
            if oncokb_order <= maximum_order:
                for gene in fusion.get_genes():
                    chromosome = cytobands.get(gene)
                    gene_url = hb.build_gene_url(gene)
                    row =  {
                        self.GENE: gene,
                        self.GENE_URL: gene_url,
                        self.CHROMOSOME: chromosome,
                        self.FRAME: fusion.get_frame(),
                        self.FUSION: fusion.get_fusion_id_new(),
                        self.MUTATION_EFFECT: fusion.get_mutation_effect(),
                        core_constants.ONCOKB: oncokb_level
                    }
                    rows.append(row)
                    gene_info_entry = gene_info_factory.get_json(
                        gene=gene,
                        summary=summaries.get(gene)
                    )
                    gene_info.append(gene_info_entry)
                    therapies = fusion.get_therapies()
                    for level in therapies.keys():
                        entries = self.build_treatment_entries(fusion, therapies)
                        treatment_opts.append(entries)
        return rows, gene_info, treatment_opts

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
        self.set_ini_default(oncokb.APPLY_CACHE, False)
        self.set_ini_default(oncokb.UPDATE_CACHE, False)
        cache_default = '/.mounts/labs/CGI/gsi/tools/djerba/oncokb_cache/scratch'
        self.set_ini_default(oncokb.ONCOKB_CACHE, cache_default)
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
