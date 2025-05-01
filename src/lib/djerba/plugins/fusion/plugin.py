"""
Plugin to generate the Fusions report section
"""

import csv
import logging
import os
import re
import json
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.fusion.tools import fusion_tools
from djerba.plugins.fusion.preprocess import prepare_fusions
from djerba.util.environment import directory_finder
from djerba.util.logger import logger
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb
import djerba.plugins.fusion.constants as fc

class FusionProcessingError(Exception):
    pass

class main(plugin_base):
    PRIORITY = 900
    PLUGIN_VERSION = '1.1.0'
    CACHE_DEFAULT = '/.mounts/labs/CGI/gsi/tools/djerba/oncokb_cache/scratch'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper = self.update_file_if_null(wrapper, fc.ARRIBA_PATH, 'arriba')
        wrapper = self.update_file_if_null(wrapper, fc.MAVIS_PATH, 'mavis')
        work_dir = self.workspace.get_work_dir()
        self.update_wrapper_if_null(wrapper, core_constants.DEFAULT_SAMPLE_INFO, fc.WHIZBAM_PROJECT, 'project')
        self.update_wrapper_if_null(wrapper, 'input_params.json', fc.ONCOTREE_CODE, 'oncotree_code')

        if os.path.exists(os.path.join(work_dir, core_constants.DEFAULT_SAMPLE_INFO)):
            sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            if wrapper.my_param_is_null(core_constants.TUMOUR_ID):
                wrapper.set_my_param(core_constants.TUMOUR_ID, sample_info.get(core_constants.TUMOUR_ID))
            if wrapper.my_param_is_null(core_constants.PROJECT):
                wrapper.set_my_param(core_constants.PROJECT, sample_info.get(core_constants.PROJECT))
        else:
            msg = 'Sample info file not found, make sure fusion parameters are in INI'
            self.logger.warning(msg)

        return wrapper.get_config()

    def extract(self, config):
        def sort_by_actionable_level(row):
            return oncokb_levels.oncokb_order(row[core_constants.ONCOKB])

        wrapper = self.get_config_wrapper(config)
        
        prepare_fusions(self.workspace.get_work_dir(), self.log_level, self.log_path).process_fusion_files(wrapper)
    
        fus_tools = fusion_tools(self.workspace.get_work_dir(), self.log_level, self.log_path)
        results, gene_info, treatment_opts = fus_tools.assemble_data(wrapper.get_my_string(fc.ONCOTREE_CODE))
        #self.workspace.write_json("test_fusions_results.json", results)

        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS] = results
        data[core_constants.MERGE_INPUTS]['gene_information_merger'] = gene_info
        data[core_constants.MERGE_INPUTS]['treatment_options_merger'] = treatment_opts

        # Processing fusions and generating blob URLs
        tsv_file_path = wrapper.get_my_string(fc.ARRIBA_PATH)
        base_dir = (directory_finder(self.log_level, self.log_path).get_base_dir())
        fusion_dir = os.path.join(base_dir, "plugins", "fusion")
        json_template_path = os.path.join(fusion_dir, fc.JSON_TO_BE_COMPRESSED)
        output_dir = self.workspace.get_work_dir()
        unique_fusions = list({item["fusion"] for item in results[fc.BODY]})
        wrapper = self.get_config_wrapper(config)
        fus_tools.construct_whizbam_links(tsv_file_path, base_dir, fusion_dir, output_dir, json_template_path, unique_fusions, config, wrapper)
        return data  

    def specify_params(self):
        discovered = [
            core_constants.PROJECT,
            fc.MAVIS_PATH,
            fc.ARRIBA_PATH,
            core_constants.TUMOUR_ID,
            fc.ONCOTREE_CODE,
            fc.WHIZBAM_PROJECT
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        # set defaults
        data_dir = directory_finder(self.log_level, self.log_path).get_data_dir()
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
        return wrapper
