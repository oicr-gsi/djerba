"""
a plugin for WGTS SNV Indel
"""

import os
import djerba.core.constants as core_constants
import djerba.plugins.wgts.snv_indel.constants as sic
import djerba.util.oncokb.constants as oncokb_constants
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.wgts.snv_indel.tools import whizbam, snv_indel_processor
from djerba.util.render_mako import mako_renderer

class main(plugin_base):
   
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'snv_indel_template.html'
    ASSAY = 'WGS'
    SEQTYPE = 'GENOME'
    GENOME = 'hg38'

    # priorities -- selected so CNV is extracted before SNV/indel but rendered after
    CONFIGURE = 700
    EXTRACT = 800
    RENDER = 700

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        # required params -- must be in INI or JSON
        # MAF input file, required for obvious reasons
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            sic.MAF_PATH,
            'variantEffectPredictor_matched'
        )
        # oncotree code is required for making OncoKB links and annotation
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            sic.ONCOTREE_CODE,
            input_params_helper.ONCOTREE_CODE
        )
        # tumour ID is required for MAF update and OncoKB annotation
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_SAMPLE_INFO,
            sic.TUMOUR_ID
        )
        # optional params with fallback value -- used only for constructing Whizbam links
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            sic.PROJECT,
            input_params_helper.PROJECT,
            fallback=sic.DEFAULT
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_SAMPLE_INFO,
            sic.NORMAL_ID,
            fallback=sic.DEFAULT
        )
        if wrapper.my_param_is_null(sic.WHIZBAM_PROJECT):
            # if whizbam project not manually configured, default to study id
            wrapper.set_my_param(sic.WHIZBAM_PROJECT, wrapper.get_my_string(sic.PROJECT))
        return wrapper.get_config()

    def extract(self, config):
        # Extraction for SNVs/indels:
        # - Construct the whizbam link prefix
        # - Preprocess the MAF file with whizbam prefix
        # - Write Whizbam links to text files in workspace for later reference
        # - Apply OncoKB annotation
        # - Read CNA values from cnv plugin output
        # - Read expression values from expression helper output
        # - Construct data for the SNV/indel table with CNVs, expression
        # - Construct data for the gene info and treatment option mergers
        # - Make the VAF plot and record as base64
        wrapper = self.get_config_wrapper(config)  
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        whizbam_url = whizbam.link_base(
            sic.WHIZBAM_BASE_URL,
            wrapper.get_my_string(sic.WHIZBAM_PROJECT),
            wrapper.get_my_string(sic.TUMOUR_ID),
            wrapper.get_my_string(sic.NORMAL_ID),
            self.SEQTYPE,
            self.GENOME
        )
        proc = snv_indel_processor(self.workspace, wrapper, self.log_level, self.log_path)
        proc.write_working_files(whizbam_url)
        data['results'] = proc.get_results()
        data['merge_inputs'] = proc.get_merge_inputs()
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        discovered = [
            sic.MAF_PATH,
            sic.ONCOTREE_CODE,
            sic.TUMOUR_ID,
            sic.NORMAL_ID,
            sic.PROJECT,
            sic.WHIZBAM_PROJECT
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(
            oncokb_constants.ONCOKB_CACHE,
            oncokb_constants.DEFAULT_CACHE_PATH
        )
        self.set_ini_default(oncokb_constants.APPLY_CACHE, False)
        self.set_ini_default(oncokb_constants.UPDATE_CACHE, False)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(core_constants.CONFIGURE_PRIORITY, self.CONFIGURE)
        self.set_ini_default(core_constants.EXTRACT_PRIORITY, self.EXTRACT)
        self.set_ini_default(core_constants.RENDER_PRIORITY, self.RENDER)
