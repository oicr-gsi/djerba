"""
Plugin for whole-genome CNV reporting
"""

import os
import djerba.core.constants as core_constants
import djerba.plugins.cnv.constants as cnv_constants
import djerba.util.oncokb.constants as oncokb_constants
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.cnv.tools import cnv_processor
from djerba.sequenza import sequenza_reader # TODO move sequenza.py to util?
from djerba.util.render_mako import mako_renderer

class main(plugin_base):
   
    PRIORITY = 800
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'cnv_template.html'

    def check_purity_is_consistent(self, cnv_purity):
        """Check CNV purity is consistent with input_params_helper value (if any)"""
        delta = 0.0000001 # tolerance for float value check
        if self.workspace.has_file(input_params_helper.INPUT_PARAMS_FILE):
            data = self.workspace.read_json(input_params_helper.INPUT_PARAMS_FILE)
            iph_purity = data.get(input_params_helper.PURITY)
            if iph_purity != None and abs(iph_purity - cnv_purity) > delta:
                msg = "Inconsistent purity values! "+\
                    "CNV plugin purity = {0}, ".format(cnv_purity)+\
                    "Input params helper purity = {0}. ".format(iph_purity)+\
                    "Update CNV and/or input params INI config so values match."
                self.logger.error(msg)
                raise RuntimeError(msg)
            else:
                self.logger.info("Purity configuration check successful")
        else:
            self.logger.info("Input params JSON not found, purity check omitted")

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            cnv_constants.ONCOTREE_CODE,
            input_params_helper.ONCOTREE_CODE
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_SAMPLE_INFO,
            cnv_constants.TUMOUR_ID,
            'tumour_id'
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            cnv_constants.SEQUENZA_PATH,
            'sequenza_by_tumor_group'
        )
        if wrapper.my_param_is_null(cnv_constants.PURITY):
            gamma = wrapper.get_my_int(cnv_constants.SEQUENZA_GAMMA)
            solution = wrapper.get_my_string(cnv_constants.SEQUENZA_SOLUTION)
            reader = sequenza_reader(wrapper.get_my_string(cnv_constants.SEQUENZA_PATH))
            purity = reader.get_purity(gamma, solution)
            wrapper.set_my_param(cnv_constants.PURITY, purity)
            self.logger.debug("Found purity {0} from sequenza results".format(purity))
        else:
            purity = wrapper.get_my_float(cnv_constants.PURITY)
            self.logger.debug("Using user-supplied purity: {0}".format(purity))
        if wrapper.get_my_boolean(cnv_constants.PURITY_CHECK):
            self.check_purity_is_consistent(purity)
        return wrapper.get_config()

    def extract(self, config):
        work_dir = self.workspace.get_work_dir()
        wrapper = self.get_config_wrapper(config)
        # write intermediate files to working directory
        processor = cnv_processor(work_dir, wrapper, self.log_level, self.log_path)
        processor.write_working_files()
        # read results from working directory into data structure
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data['results'] = processor.get_results()
        data['merge_inputs'] = processor.get_merge_inputs()
        return data
    
    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        required = [
            cnv_constants.SEQUENZA_GAMMA,
            cnv_constants.SEQUENZA_SOLUTION,
        ]
        for key in required:
            self.add_ini_required(key)
        discovered = [
            cnv_constants.ONCOTREE_CODE,
            cnv_constants.SEQUENZA_PATH,
            cnv_constants.PURITY,
            cnv_constants.TUMOUR_ID
        ]
        self.set_ini_default(
            oncokb_constants.ONCOKB_CACHE,
            oncokb_constants.DEFAULT_CACHE_PATH
        )
        self.set_ini_default(oncokb_constants.APPLY_CACHE, False)
        self.set_ini_default(oncokb_constants.UPDATE_CACHE, False)
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(cnv_constants.PURITY_CHECK, True)
        self.set_priority_defaults(self.PRIORITY)
