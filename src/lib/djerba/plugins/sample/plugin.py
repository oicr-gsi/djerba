"""
Sample plugin for WGTS
"""
import os
import logging
import json
from decimal import Decimal
from mako.lookup import TemplateLookup
import djerba.plugins.sample.constants as constants
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer
import djerba.util.input_params_tools as input_params_tools

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError as err:
    raise RuntimeError('QC-ETL import failure! Try checking python versions') from err

class main(plugin_base):

    PLUGIN_VERSION = '1.0.0'
    PRIORITY = 500
    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"
    
    def specify_params(self):
        discovered = [
            constants.ONCOTREE,
            constants.SAMPLE_TYPE,
            constants.CALLABILITY,
            constants.COVERAGE,
            constants.PURITY,
            constants.PLOIDY,
            core_constants.TUMOUR_ID,
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()

        # Get input_data.json if it exists; else return None
        input_data = input_params_tools.get_input_params_json(self)
        if input_data == None:
            msg = "Input_params.json does not exist. Parameters must be set manually."
            self.logger.warning(msg)

        # FIRST PASS: Get the input parameters
        if wrapper.my_param_is_null(constants.ONCOTREE):
            wrapper.set_my_param(constants.ONCOTREE, input_data[constants.ONCOTREE])
        if wrapper.my_param_is_null(constants.SAMPLE_TYPE):
            wrapper.set_my_param(constants.SAMPLE_TYPE, input_data[constants.SAMPLE_TYPE])

        wrapper = self.fill_param_if_null(wrapper, constants.PURITY, "purity_ploidy.json")
        wrapper = self.fill_param_if_null(wrapper, constants.PLOIDY, "purity_ploidy.json")

        # Get tumour_id from sample info:
        if wrapper.my_param_is_null(core_constants.TUMOUR_ID):
            info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            tumour_id = info[constants.TUMOUR_ID]
            wrapper.set_my_param(core_constants.TUMOUR_ID, tumour_id)
        
        tumour_id = config[self.identifier][core_constants.TUMOUR_ID]
        # SECOND PASS: Get files based on input parameters
        if wrapper.my_param_is_null(constants.CALLABILITY):
            wrapper.set_my_param(constants.CALLABILITY, self.fetch_callability_etl_data(tumour_id))        
        if wrapper.my_param_is_null(constants.COVERAGE):
            wrapper.set_my_param(constants.COVERAGE, self.fetch_coverage_etl_data(tumour_id))

        return wrapper.get_config()
    
    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        # multiply purity by 100 to get a percentage, and round to the nearest integer
        purity = config[self.identifier][constants.PURITY]
        if purity not in ["NA", "N/A", "na", "n/a", "N/a", "Na"]:
            purity = int(round(float(purity)*100, 0))
        results = {
                constants.ONCOTREE_CODE: config[self.identifier][constants.ONCOTREE],
                constants.TUMOUR_SAMPLE_TYPE : config[self.identifier][constants.SAMPLE_TYPE],
                constants.EST_CANCER_CELL_CONTENT : purity,
                constants.EST_PLOIDY: config[self.identifier][constants.PLOIDY],
                constants.CALLABILITY_PERCENT: config[self.identifier][constants.CALLABILITY],
                constants.COVERAGE_MEAN: config[self.identifier][constants.COVERAGE]    
        }
        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name('sample_template.html', data)

    def fetch_callability_etl_data(self,tumour_id):
        etl_cache = QCETLCache(self.QCETL_CACHE)
        cached_callabilities = etl_cache.mutectcallability.mutectcallability
        columns_of_interest = gsiqcetl.column.MutetctCallabilityColumn
        data = cached_callabilities.loc[
            (cached_callabilities[columns_of_interest.GroupID] == tumour_id),
            [columns_of_interest.GroupID, columns_of_interest.Callability]
            ]
        if len(data) > 0:
            callability = round(data.iloc[0][columns_of_interest.Callability].item() * 100,1)
            return callability
        else:
            msg = "Djerba couldn't find the callability associated with tumour_id {0} in QC-ETL. ".format(tumour_id)
            self.logger.error(msg)
            raise MissingQCETLError(msg)
        
    def fetch_coverage_etl_data(self,tumour_id):
        etl_cache = QCETLCache(self.QCETL_CACHE)
        cached_coverages = etl_cache.bamqc4merged.bamqc4merged
        columns_of_interest = gsiqcetl.column.BamQc4MergedColumn
        data = cached_coverages.loc[
            (cached_coverages[columns_of_interest.GroupID] == tumour_id),
            [columns_of_interest.GroupID, columns_of_interest.CoverageDeduplicated]
            ]
        if len(data) > 0:
            coverage_value = round(data.iloc[0][columns_of_interest.CoverageDeduplicated].item(),1)
            return(coverage_value)
        else:
            msg = "Djerba couldn't find the coverage associated with tumour_id {0} in QC-ETL. ".format(tumour_id)
            self.logger.debug(msg)
            raise MissingQCETLError(msg)

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

class MissingQCETLError(Exception):
    pass 
