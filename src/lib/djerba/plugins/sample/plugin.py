"""
Sample plugin for WGTS
"""
import math
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
from djerba.util.logger import logger


try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError as err:
    raise RuntimeError('QC-ETL import failure! Try checking python versions') from err

class main(plugin_base):

    PLUGIN_VERSION = '1.0.0'
    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"
    
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
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        
        # Default parameters for priorities
        self.set_ini_default('configure_priority', 100)
        self.set_ini_default('extract_priority', 500)
        self.set_ini_default('render_priority', 500)


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

        # Fetch tumour_id and donor
        donor = config[self.identifier][constants.DONOR]
        tumour_id = config[self.identifier][core_constants.TUMOUR_ID]
        # SECOND PASS: Get files based on input parameters
        if wrapper.my_param_is_null(constants.CALLABILITY):
            wrapper.set_my_param(constants.CALLABILITY, self.fetch_callability_etl_data(donor, tumour_id))        
        if wrapper.my_param_is_null(constants.COVERAGE):
            wrapper.set_my_param(constants.COVERAGE, self.fetch_coverage_etl_data(donor, tumour_id))

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
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name('sample_template.html', data)

    def fetch_callability_etl_data(self, donor, tumour_id):
        etl_cache = QCETLCache(self.QCETL_CACHE)
        cached_callabilities = etl_cache.mutectcallability.mutectcallability
        columns_of_interest = gsiqcetl.column.MutetctCallabilityColumn
        # Note: donor and tumour ID are both not unique, but together are unique. Filter on both.
        # One donor can have multiple tumour IDs; one tumour ID can be associated with multiple donors
        # But one donor will not have a duplicate tumour IDs
        data = cached_callabilities.loc[
            (cached_callabilities[columns_of_interest.GroupID] == tumour_id) & # filter on tumour_id
            (cached_callabilities[columns_of_interest.Donor] == donor), # filter also on donor
            [columns_of_interest.GroupID, columns_of_interest.Donor, columns_of_interest.Callability]
            ]
        if len(data) == 1:
            # Round down to one decimal place
            callability = math.floor(data.iloc[0][columns_of_interest.Callability].item() * 1000) / 10
            callability_threshold = 75
            if callability < callability_threshold:
                msg = f"Callability is below the reportable threshold: {callability:.1f}% < {callability_threshold}%"
                self.logger.warning(msg)
            return callability
        elif len(data) > 1:
            msg = "Djerba found more than one callability associated with donor {0} and tumour_id {1} in QC-ETL. Double check that the callability found by Djerba is correct; if not, may have to manually specify the callability.".format(donor, tumour_id)
            self.logger.warning(msg)
        else:
            msg = "Djerba couldn't find the callability associated with donor {0} and tumour_id {1} in QC-ETL.".format(donor, tumour_id)
            self.logger.error(msg)
            raise MissingQCETLError(msg)
        
    def fetch_coverage_etl_data(self, donor, tumour_id):
        etl_cache = QCETLCache(self.QCETL_CACHE)
        cached_coverages = etl_cache.bamqc4merged.bamqc4merged
        columns_of_interest = gsiqcetl.column.BamQc4MergedColumn
        # Note: donor and tumour ID are both not unique, but together are unique. Filter on both.
        # One donor can have multiple tumour IDs; one tumour ID can be associated with multiple donors
        # But one donor will not have a duplicate tumour IDs
        data = cached_coverages.loc[
            (cached_coverages[columns_of_interest.GroupID] == tumour_id) &
            (cached_coverages[columns_of_interest.Donor] == donor),
            [columns_of_interest.GroupID, columns_of_interest.Donor, columns_of_interest.CoverageDeduplicated]
            ]
        if len(data) == 1:
            coverage_value = round(data.iloc[0][columns_of_interest.CoverageDeduplicated].item(),1)
            return(coverage_value)
        elif len(data) > 1:
            msg = "Djerba found more than one coverage associated with donor {0} and tumour_id {1} in QC-ETL. Double check that the coverage found by Djerba is correct; if not, may have to manually specify the coverage.".format(donor, tumour_id)
            self.logger.warning(msg)

        else:
            msg = "Djerba couldn't find the coverage associated with donor {0} and tumour_id {1} in QC-ETL. ".format(donor, tumour_id)
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
