"""
Plugin to generate the Fusions report section
"""

import csv
import logging
import os
import re
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.fusion.tools import fusion_reader, prepare_fusions
from djerba.util.environment import directory_finder
from djerba.util.html import html_builder as hb
from djerba.util.logger import logger
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb
import djerba.plugins.fusion.constants as fc

class main(plugin_base):

    PRIORITY = 900
    PLUGIN_VERSION = '1.1.0'
    CACHE_DEFAULT = '/.mounts/labs/CGI/gsi/tools/djerba/oncokb_cache/scratch'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper = self.update_file_if_null(wrapper, fc.ARRIBA_PATH, 'arriba')
        wrapper = self.update_file_if_null(wrapper, fc.MAVIS_PATH, 'mavis')
        self.update_wrapper_if_null(wrapper, 'input_params.json', fc.ONCOTREE_CODE, 'oncotree_code')
        if wrapper.my_param_is_null(core_constants.TUMOUR_ID):
            sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            wrapper.set_my_param(core_constants.TUMOUR_ID, sample_info.get(core_constants.TUMOUR_ID))
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        prepare_fusions( self.workspace.get_work_dir(), self.log_level, self.log_path).process_fusion_files(wrapper)
        fus_reader = fusion_reader( self.workspace.get_work_dir(), self.log_level, self.log_path )
        total_fusion_genes = fus_reader.get_total_fusion_genes()
        gene_pair_fusions = fus_reader.get_fusions()
        if gene_pair_fusions is not None:
            outputs = fus_reader.fusions_to_json(gene_pair_fusions, wrapper.get_my_string(fc.ONCOTREE_CODE))
            [rows, gene_info, treatment_opts] = outputs
            # rows are already sorted by the fusion reader
            max_actionable = oncokb_levels.oncokb_order('P')
            rows = list(filter(lambda x: oncokb_levels.oncokb_order(x[core_constants.ONCOKB]) <= max_actionable, rows))
            # distinct_oncogenic_genes = len(set([row.get(fc.GENE) for row in rows]))
            results = {
                fc.TOTAL_VARIANTS: total_fusion_genes,
                fc.CLINICALLY_RELEVANT_VARIANTS: fus_reader.get_total_oncokb_fusions(),
                fc.NCCN_RELEVANT_VARIANTS: fus_reader.get_total_nccn_fusions(),
                fc.BODY: rows
            }
        else:
            results = {
                fc.TOTAL_VARIANTS: 0,
                fc.CLINICALLY_RELEVANT_VARIANTS: 0,
                fc.NCCN_RELEVANT_VARIANTS: 0,
                fc.BODY: []
            }
            gene_info = []
            treatment_opts = []
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS] = results
        data[core_constants.MERGE_INPUTS]['gene_information_merger'] = gene_info
        data[core_constants.MERGE_INPUTS]['treatment_options_merger'] = treatment_opts
        return data

    def specify_params(self):
        discovered = [
            fc.MAVIS_PATH,
            fc.ARRIBA_PATH,
            core_constants.TUMOUR_ID,
            fc.ONCOTREE_CODE
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        #set defaults
        data_dir = directory_finder(self.log_level, self.log_path).get_data_dir()
        self.set_ini_default(fc.ENTREZ_CONVERSION_PATH, os.path.join(data_dir, fc.ENTRCON_NAME))
        self.set_ini_default(fc.MIN_FUSION_READS, 20)
        self.set_ini_default(oncokb.APPLY_CACHE, False)
        self.set_ini_default(oncokb.UPDATE_CACHE, False)
        self.set_ini_default(oncokb.ONCOKB_CACHE, self.CACHE_DEFAULT)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(fc.MAKO_TEMPLATE_NAME, data)

    def update_file_if_null(self, wrapper, ini_name, path_info_workflow_name):
        if wrapper.my_param_is_null(ini_name):
            self.logger.debug("Updating {0} with path info for {1}".format(ini_name, path_info_workflow_name))
            path_info = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
            file_path = path_info.get(path_info_workflow_name)
            if file_path == None:
                msg = "Cannot find {0} path for fusion input".format(path_info_workflow_name)
                self.logger.error(msg)
                raise RuntimeError(msg)
            wrapper.set_my_param(ini_name, file_path)
        return(wrapper)
