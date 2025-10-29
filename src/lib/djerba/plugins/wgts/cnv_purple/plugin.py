"""
a plugin for WGTS CNV, based on PURPLE
"""

# IMPORTS
import os

import djerba.core.constants as core_constants
import djerba.plugins.wgts.cnv_purple.constants as pc
import djerba.util.oncokb.constants as oc
from djerba.helpers.input_params_helper.helper import main as iph
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.wgts.cnv_purple.legacy_tools import cnv_processor
from djerba.plugins.wgts.cnv_purple.purple_tools import purple_processor
from djerba.util.oncokb.annotator import annotator_factory
from djerba.util.render_mako import mako_renderer


class main(plugin_base):
    PLUGIN_VERSION = '0.1.0'
    CONFIGURE = 80
    EXTRACT = 700
    RENDER = 800

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        key_mapping = {
            iph.ASSAY: iph.ASSAY,
            oc.ONCOTREE_CODE: iph.ONCOTREE_CODE,
            pc.WHIZBAM_PROJECT: iph.PROJECT
        }
        self.logger.debug("Finding config params")
        for k, v in key_mapping.items():
            wrapper = self.update_wrapper_if_null(wrapper, iph.INPUT_PARAMS_FILE, k, v)
        wrapper = self.update_wrapper_if_null(
            wrapper, core_constants.DEFAULT_SAMPLE_INFO, core_constants.TUMOUR_ID
        )
        wrapper = self.update_wrapper_if_null(
            wrapper, core_constants.DEFAULT_PATH_INFO, pc.PURPLE_DIR, pc.PURPLE
        )
        work_dir = self.workspace.get_work_dir()
        processor = purple_processor(work_dir, self.log_level, self.log_path)
        purity_ploidy = processor.read_purity_ploidy(wrapper.get_my_string(pc.PURPLE_DIR))
        self.workspace.write_json(pc.PURITY_PLOIDY, purity_ploidy)
        self.logger.debug("Wrote purity/ploidy to workspace: {0}".format(purity_ploidy))
        return wrapper.get_config()

    def extract(self, config):
        work_dir = self.workspace.get_work_dir()
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        purity_ploidy = self.workspace.read_json(pc.PURITY_PLOIDY)
        self.logger.debug("Read purity/ploidy from workspace: {0}".format(purity_ploidy))
        ploidy = purity_ploidy[pc.PLOIDY]
        tumour_id = wrapper.get_my_string(core_constants.TUMOUR_ID)

        # process purple files
        self.logger.debug("Starting purple data processing")
        plot9_verbose = wrapper.get_my_boolean(pc.PLOTNINE_VERBOSE)
        processor = purple_processor(work_dir, self.log_level, self.log_path, plot9_verbose)
        self.logger.debug("Finding PURPLE files in directory")
        purple_files = processor.find_purple_files(wrapper.get_my_string(pc.PURPLE_DIR))
        self.logger.debug("Evaluating purity fit")
        processor.consider_purity_fit(purple_files[pc.PURPLE_PURITY_RANGE])
        self.logger.debug("Converting data format")
        processor.convert_purple_to_gistic(purple_files[pc.PURPLE_GENE], tumour_id, ploidy)
        self.logger.debug("Analyzing genome segments")
        whizbam_link = processor.construct_whizbam_link(
            wrapper.get_my_string(pc.WHIZBAM_PROJECT),
            tumour_id,
        )
        cnv_plot_base64 = processor.analyze_segments(purple_files[pc.PURPLE_CNV],
                                                     purple_files[pc.PURPLE_SEG],
                                                     whizbam_link,
                                                     purity_ploidy[pc.PURITY],
                                                     ploidy)
        processor.write_copy_states(tumour_id)

        # write alternate solutions launcher JSON
        if os.path.exists(os.path.join(work_dir, core_constants.DEFAULT_PATH_INFO)):
            self.logger.debug("Writing alternate solutions JSON")
            purple_alternate = processor.write_purple_alternate_launcher(
                self.workspace.read_json(core_constants.DEFAULT_PATH_INFO))
            self.workspace.write_json(pc.PURPLE_ALT, purple_alternate)
        else:
            self.logger.debug("Omitting alternate solutions (path info not available)")

        # run oncokb annotator
        self.logger.debug("Finding OncoKB variant annotation")
        factory = annotator_factory(self.log_level, self.log_path)
        factory.get_annotator(work_dir, wrapper).annotate_cna()

        # run CNV tools
        self.logger.debug("Collating purple results")
        cnv = cnv_processor(work_dir, wrapper, self.log_level, self.log_path)
        data[core_constants.RESULTS] = cnv.get_results()
        data[core_constants.RESULTS][pc.CNV_PLOT] = cnv_plot_base64
        data[core_constants.MERGE_INPUTS] = cnv.get_merge_inputs()
        self.logger.debug("Finished purple extraction")
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.TEMPLATE_NAME, data)

    def specify_params(self):
        discovered = [
            iph.ASSAY,
            core_constants.TUMOUR_ID,
            oc.ONCOTREE_CODE,
            pc.WHIZBAM_PROJECT,
            pc.PURPLE_DIR
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(
            oc.ONCOKB_CACHE,
            oc.DEFAULT_CACHE_PATH
        )
        self.set_ini_default(oc.APPLY_CACHE, False)
        self.set_ini_default(oc.UPDATE_CACHE, False)
        self.set_ini_default(pc.PLOTNINE_VERBOSE, False)
        self.set_ini_default(core_constants.ATTRIBUTES, core_constants.CLINICAL)
        self.set_ini_default(core_constants.CONFIGURE_PRIORITY, self.CONFIGURE)
        self.set_ini_default(core_constants.EXTRACT_PRIORITY, self.EXTRACT)
        self.set_ini_default(core_constants.RENDER_PRIORITY, self.RENDER)
