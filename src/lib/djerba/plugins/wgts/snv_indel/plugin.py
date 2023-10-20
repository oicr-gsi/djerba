"""
a plugin for WGTS SNV Indel
"""

import os
import djerba.core.constants as core_constants
import djerba.plugins.wgts.snv_indel.constants as sic
import djerba.util.oncokb.constants as oncokb_constants
from djerba.plugins.base import plugin_base
from djerba.plugins.wgts.snv_indel.tools import whizbam, snv_indel_processor
from djerba.util.render_mako import mako_renderer

class main(plugin_base):
   
    PRIORITY = 700
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'snv_indel_template.html'
    ASSAY = 'WGS'
    SEQTYPE = 'GENOME'
    GENOME = 'hg38'
    HAS_EXPRESSION_DATA = False
    
    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        # TODO process the config parameters
        return config  

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
        work_dir = self.workspace.get_work_dir()
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        oncotree_code = wrapper.get_my_string(sic.ONCOTREE_CODE)
        cbio_id = wrapper.get_my_string(sic.STUDY_ID)
        tumour_id = wrapper.get_my_string(sic.TUMOUR_ID)
        normal_id = wrapper.get_my_string(sic.NORMAL_ID)
        maf_path = wrapper.get_my_string(sic.MAF_PATH)
        whizbam_url = whizbam.link_base(
            sic.WHIZBAM_BASE_URL,
            cbio_id,
            tumour_id,
            normal_id,
            self.SEQTYPE,
            self.GENOME
        )
        proc = snv_indel_processor(work_dir, wrapper, self.log_level, self.log_path)
        proc.write_working_files(whizbam_url)
        data['results'] = proc.get_results()
        data['merge_inputs'] = proc.get_merge_inputs()
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        required = [
            sic.MAF_PATH,
            sic.ONCOTREE_CODE,
            sic.TUMOUR_ID,
            sic.NORMAL_ID,
            sic.STUDY_ID,
            sic.HAS_EXPRESSION_DATA
        ]
        for key in required:
            self.add_ini_required(key)
        self.set_ini_default(
            oncokb_constants.ONCOKB_CACHE,
            oncokb_constants.DEFAULT_CACHE_PATH
        )
        self.set_ini_default(oncokb_constants.APPLY_CACHE, False)
        self.set_ini_default(oncokb_constants.UPDATE_CACHE, False)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)
