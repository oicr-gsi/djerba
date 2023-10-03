"""
Plugin for whole-genome CNV reporting
"""

import os
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb_constants
from djerba.plugins.base import plugin_base
from djerba.plugins.cnv.tools import cnv_processor
from djerba.sequenza import sequenza_reader # TODO move sequenza.py to util?
from djerba.util.render_mako import mako_renderer

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'cnv_template.html'

    # INI param names
    # these params are also used by other plugins; TODO remove reundancy
    SEQUENZA_PATH = 'sequenza_path'
    SEQUENZA_GAMMA = 'sequenza_gamma'
    SEQUENZA_SOLUTION = 'sequenza_solution'
    PURITY = 'purity'
    TUMOUR_ID = 'tumour_id'
    ONCOTREE_CODE = 'oncotree_code'

    # keys for JSON output
    ALTERATION = 'Alteration'
    CHROMOSOME = 'Chromosome'
    EXPRESSION_PERCENTILE = 'Expression Percentile'
    GENE = 'Gene'
    GENE_URL = 'Gene_URL'
    ONCOKB = core_constants.ONCOKB
    HAS_EXPRESSION_DATA = 'Has expression data'

    # constants for rendering
    PERCENT_GENOME_ALTERED = 'percent_genome_altered'
    TOTAL_VARIANTS = 'total_variants'
    CLINICALLY_RELEVANT_VARIANTS = 'clinically_relevant_variants'
    
    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        # TODO get sequenza path from provenenance helper JSON
        if wrapper.my_param_is_null(self.PURITY):
            gamma = config.get_my_int(self.SEQUENZA_GAMMA)
            solution = config.get_my_string(self.SEQUENZA_SOLUTION)
            reader = sequenza_reader(config.get_my_string(self.SEQUENZA_PATH))
            purity = reader.get_purity(gamma, solution)
            wrapper.set_my_param(self.PURITY, purity)
            self.logger.debug("Found purity {0} from sequenza results".format(purity))
        else:
            purity = wrapper.get_my_float(self.PURITY)
            self.logger.debug("Using user-supplied purity: {0}".format(purity))
        return wrapper.get_config()

    def extract(self, config):
        work_dir = self.workspace.get_work_dir()
        wrapper = self.get_config_wrapper(config)
        # write intermediate files to working directory
        processor = cnv_processor(work_dir, wrapper, self.log_level, self.log_path)
        processor.run()
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
            self.SEQUENZA_FILE,
            self.SEQUENZA_GAMMA,
            self.SEQUENZA_SOLUTION,
            self.TUMOUR_ID,
            self.ONCOTREE_CODE
        ]
        for key in required:
            self.add_ini_required(key)
        discovered = [
            self.PURITY
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
        self.set_priority_defaults(self.PRIORITY)
