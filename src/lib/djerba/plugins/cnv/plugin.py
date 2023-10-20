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

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        if wrapper.my_param_is_null(cnv_constants.ONCOTREE_CODE):
            if self.workspace.has_file(input_params_helper.INPUT_PARAMS_FILE):
                data = self.workspace.read_json(input_params_helper.INPUT_PARAMS_FILE)
                oncotree_code = data[input_params_helper.ONCOTREE_CODE]
                wrapper.set_my_param(cnv_constants.ONCOTREE_CODE, oncotree_code)
            else:
                msg = "Cannot find Oncotree code; must be manually specified or "+\
                    "given in {0}".format(input_params_helper.INPUT_PARAMS_FILE)
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        if wrapper.my_param_is_null(cnv_constants.TUMOUR_ID):
            if self.workspace.has_file(core_constants.DEFAULT_SAMPLE_INFO):
                data = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
                sequenza_path = data['tumour_id']
                wrapper.set_my_param(cnv_constants.TUMOUR_ID, sequenza_path)
            else:
                msg = "Cannot find tumour ID; must be manually specified or "+\
                    "given in {0}".format(core_constants.DEFAULT_SAMPLE_INFO)
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        if wrapper.my_param_is_null(cnv_constants.SEQUENZA_PATH):
            if self.workspace.has_file(core_constants.DEFAULT_PATH_INFO):
                data = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
                sequenza_path = data['sequenza_by_tumor_group']
                wrapper.set_my_param(cnv_constants.SEQUENZA_PATH, sequenza_path)
            else:
                msg = "Cannot find Sequenza input path; must be manually specified or "+\
                    "given in {0}".format(core_constants.DEFAULT_PATH_INFO)
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
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
        self.set_ini_default(cnv_constants.HAS_EXPRESSION_DATA, True)
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)
