"""
Sample plugin for WGTS
"""
import math
import os
import logging
import json
from decimal import Decimal
from importlib import import_module
from importlib.util import find_spec
from mako.lookup import TemplateLookup
import djerba.plugins.sample.constants as constants
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.gsiqcetl import gsiqcetl_plugin_base, MissingQCETLError
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer
from djerba.util.logger import logger
from djerba.util.validator import path_validator


class main(gsiqcetl_plugin_base):

    PLUGIN_VERSION = '1.0.0'
    QCETL_CACHE_DEFAULT = "/scratch2/groups/gsi/production/qcetl_v1"
    QCETL_CACHE_KEY = 'qcetl_cache'


    def specify_params(self):
        discovered = [
            constants.ONCOTREE,
            constants.SAMPLE_TYPE,
            constants.CALLABILITY,
            constants.COVERAGE,
            constants.DONOR,
            constants.PURITY,
            constants.PLOIDY,
            core_constants.TUMOUR_ID,
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        
        # Default parameters
        self.set_ini_default('configure_priority', 100)
        self.set_ini_default('extract_priority', 500)
        self.set_ini_default('render_priority', 500)
        self.set_ini_default(constants.CALLABILITY_WARNING, False)
        self.set_ini_default(self.QCETL_CACHE_KEY, self.QCETL_CACHE_DEFAULT)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()

        # Get input_data.json if it exists; else return None
        input_data = self.workspace.read_maybe_input_params()

        # FIRST PASS: Get the input parameters
        for key in [constants.ONCOTREE, constants.SAMPLE_TYPE]:
            if wrapper.my_param_is_null(key):
                if input_data != None:
                    wrapper.set_my_param(key, input_data[key])
                else:
                    msg = "Cannot find {0} in manual config or input_params.json".format(key)
                    self.logger.error(msg)
                    raise RuntimeError(msg)
        wrapper = self.fill_param_if_null(wrapper, constants.PURITY, "purity_ploidy.json")
        wrapper = self.fill_param_if_null(wrapper, constants.PLOIDY, "purity_ploidy.json")

        # Get tumour_id and donor
        for key in [core_constants.TUMOUR_ID, constants.DONOR]:
            if wrapper.my_param_is_null(key):
                if os.path.exists(os.path.join(work_dir,core_constants.DEFAULT_SAMPLE_INFO)):
                    info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
                    wrapper.set_my_param(key, info[key])
                else:
                    msg = "Cannot find {0} in manual config or sample_info.json".format(key)
                    self.logger.error(msg)
                    raise RuntimeError(msg)

        # Store config parameters as variables for convenience
        donor = wrapper.get_my_string(constants.DONOR)
        tumour_id = wrapper.get_my_string(core_constants.TUMOUR_ID)
        ignore_warning = wrapper.get_my_boolean(constants.CALLABILITY_WARNING)
        cache_path = wrapper.get_my_string(self.QCETL_CACHE_KEY)

        # SECOND PASS: Get files based on input parameters
        if self.gsiqcetl_ok():
            etl_cache = self.get_qcetl_cache(cache_path)
            if wrapper.my_param_is_null(constants.CALLABILITY):
                callability = self.fetch_callability_etl_data(etl_cache, donor, tumour_id, ignore_warning)
                wrapper.set_my_param(constants.CALLABILITY, callability)
            if wrapper.my_param_is_null(constants.COVERAGE):
                coverage = self.fetch_coverage_etl_data(etl_cache, donor, tumour_id)
                wrapper.set_my_param(constants.COVERAGE, coverage)
        else:
            msg = "GSI-QC-ETL not available, omitting coverage/callability fetch"
            self.logger.info(msg)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        # multiply purity by 100 to get a percentage, and round to the nearest integer
        purity = config[self.identifier][constants.PURITY]
        if purity not in ["NA", "N/A", "na", "n/a", "N/a", "Na"]:
            purity = float(purity)
            # check purity is within the valid range (0 <= purity <= 1)
            if not (0 <= purity <= 1):
                raise ValueError(f"Invalid purity value: {purity}. Must be between 0 and 1 (inclusive).")
            purity = int(round(purity*100, 0))
        results = {
                constants.ONCOTREE_CODE: config[self.identifier][constants.ONCOTREE],
                constants.TUMOUR_SAMPLE_TYPE : config[self.identifier][constants.SAMPLE_TYPE],
                constants.EST_CANCER_CELL_CONTENT : purity,
                constants.EST_PLOIDY: config[self.identifier][constants.PLOIDY],
                constants.CALLABILITY_PERCENT: config[self.identifier][constants.CALLABILITY],
                constants.COVERAGE_MEAN: config[self.identifier][constants.COVERAGE]    
        }
        data['results'] = results
        self.workspace.write_json(constants.QC_SAMPLE_INFO, results)
        return data

    def render(self, data):
        if not data.get('attributes') or data['attributes'] == ['']:
            data['attributes'] = ['clinical']
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name('sample_template.html', data)

    def fill_param_if_null(self, wrapper, param, input_param_file):
        if wrapper.my_param_is_null(param):
            if self.workspace.has_file(input_param_file):
                data = self.workspace.read_json(input_param_file)
                param_value = data[param]
                wrapper.set_my_param(param, param_value)
            else:
                msg = "Cannot find {0}; must be manually specified or ".format(param)+\
                        "given in {0}".format(input_param_file)
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        return(wrapper)

class LowCallabilityError(Exception):
    pass
