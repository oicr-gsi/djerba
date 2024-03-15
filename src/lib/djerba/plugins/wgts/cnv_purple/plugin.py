"""
a plugin for WGTS CNV, based on PURPLE
"""

# IMPORTS
import os

import djerba.core.constants as core_constants
import djerba.plugins.wgts.cnv_purple.constants as cc
import djerba.util.oncokb.constants as oc
from djerba.helpers.input_params_helper.helper import main as iph
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.cnv.tools import cnv_processor
from djerba.plugins.wgts.cnv_purple.purple_tools import process_purple, fetch_purple_purity, construct_whizbam_link
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

        wrapper = self.fill_param_if_null(wrapper, iph.ASSAY, iph.ASSAY, iph.INPUT_PARAMS_FILE)
        wrapper = self.fill_param_if_null(wrapper, iph.ONCOTREE_CODE, oc.ONCOTREE_CODE, iph.INPUT_PARAMS_FILE)
        wrapper = self.fill_param_if_null(wrapper, iph.PROJECT, cc.WHIZBAM_PROJECT, iph.INPUT_PARAMS_FILE)

        wrapper = self.fill_param_if_null(wrapper, core_constants.TUMOUR_ID, core_constants.TUMOUR_ID,
                                          core_constants.DEFAULT_SAMPLE_INFO)
        wrapper = self.fill_file_if_null(wrapper, cc.PURPLE, cc.PURPLE_ZIP, core_constants.DEFAULT_PATH_INFO)

        purity_ploidy = fetch_purple_purity(wrapper.get_my_string(cc.PURPLE_ZIP))
        self.workspace.write_json(cc.PURITY_PLOIDY, purity_ploidy)
        self.logger.debug("Wrote path info to workspace: {0}".format(purity_ploidy))

        return wrapper.get_config()

    def extract(self, config):
        work_dir = self.workspace.get_work_dir()
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

        purity_ploidy = self.workspace.read_json(cc.PURITY_PLOIDY)
        ploidy = purity_ploidy[cc.PLOIDY]

        # process purple files
        purple_cnv = process_purple(work_dir)
        purple_files = purple_cnv.unzip_purple(wrapper.get_my_string(cc.PURPLE_ZIP))
        purple_cnv.consider_purity_fit(purple_files[cc.PURPLE_PURITY_RANGE])
        purple_cnv.convert_purple_to_gistic(purple_files[cc.PURPLE_GENE], ploidy)
        cnv_plot_base64 = purple_cnv.analyze_segments(purple_files[cc.PURPLE_CNV],
                                                      purple_files[cc.PURPLE_SEG],
                                                      construct_whizbam_link(wrapper.get_my_string(cc.WHIZBAM_PROJECT),
                                                                             wrapper.get_my_string(
                                                                                 core_constants.TUMOUR_ID)),
                                                      purity_ploidy[cc.PURITY],
                                                      ploidy)

        # write alternate solutions launcher JSON
        if os.path.exists(os.path.join(work_dir, core_constants.DEFAULT_PATH_INFO)):
            purple_alternate = purple_cnv.write_purple_alternate_launcher(
                self.workspace.read_json(core_constants.DEFAULT_PATH_INFO))
            self.workspace.write_json(cc.PURPLE_ALT, purple_alternate)

        # run oncokb annotator
        factory = annotator_factory(self.log_level, self.log_path)
        factory.get_annotator(work_dir, wrapper).annotate_cna()

        # run CNV tools
        cnv = cnv_processor(work_dir, wrapper, self.log_level, self.log_path)
        data[core_constants.RESULTS] = cnv.get_results()
        data[core_constants.RESULTS][cc.CNV_PLOT] = cnv_plot_base64
        data[core_constants.MERGE_INPUTS] = cnv.get_merge_inputs()

        return data

    def fill_file_if_null(self, wrapper, workflow_name, ini_param, path_info):
        if wrapper.my_param_is_null(ini_param):
            if self.workspace.has_file(path_info):
                path_info = self.workspace.read_json(path_info)
                workflow_path = path_info.get(workflow_name)
                if workflow_path is None:
                    msg = 'Cannot find {0}'.format(ini_param)
                    self.logger.error(msg)
                    raise RuntimeError(msg)
                wrapper.set_my_param(ini_param, workflow_path)
        return wrapper

    def fill_param_if_null(self, wrapper, param, ini_param, input_param_file):
        if wrapper.my_param_is_null(ini_param):
            if self.workspace.has_file(input_param_file):
                data = self.workspace.read_json(input_param_file)
                param_value = data[param]
                wrapper.set_my_param(ini_param, param_value)
            else:
                msg = "Cannot find {0}; must be manually specified or ".format(ini_param) + \
                      "given in {0}".format(input_param_file)
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        return wrapper

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(cc.TEMPLATE_NAME, data)

    def specify_params(self):
        discovered = [
            iph.ASSAY,
            core_constants.TUMOUR_ID,
            oc.ONCOTREE_CODE,
            cc.WHIZBAM_PROJECT,
            cc.PURPLE_ZIP
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(
            oc.ONCOKB_CACHE,
            oc.DEFAULT_CACHE_PATH
        )
        self.set_ini_default(oc.APPLY_CACHE, False)
        self.set_ini_default(oc.UPDATE_CACHE, False)
        self.set_ini_default(core_constants.ATTRIBUTES, core_constants.CLINICAL)
        self.set_ini_default(core_constants.CONFIGURE_PRIORITY, self.CONFIGURE)
        self.set_ini_default(core_constants.EXTRACT_PRIORITY, self.EXTRACT)
        self.set_ini_default(core_constants.RENDER_PRIORITY, self.RENDER)
