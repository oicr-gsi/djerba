import os
import csv
import logging
import json
from decimal import Decimal

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.tar.sample.constants as constants
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer
try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError as err:
    raise RuntimeError('QC-ETL import failure! Try checking python versions') from err

class main(plugin_base):

    PLUGIN_VERSION = '1.0.0'
    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"
    
    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        
        # Get input_data.json if it exists; else return None
        input_data = self.workspace.read_maybe_input_params()

        # Get various IDs
        keys = [constants.ONCOTREE, constants.KNOWN_VARIANTS, constants.SAMPLE_TYPE]
        key_mapping = {k:k for k in keys} # mapping from INI keys to input_params.json keys
        key_mapping[constants.GROUP_ID] = constants.TUMOUR_ID
        for key,val in key_mapping.items():
            if wrapper.my_param_is_null(key):
                if input_data != None:
                    wrapper.set_my_param(key, input_data[val])
                else:
                    msg = "Cannot find {0} in manual config or input_params.json".format(key)
                    self.logger.error(msg)
                    raise RuntimeError(msg)
        

        # Get files from path_info.json
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            constants.ICHORCNA_FILE,
            constants.WF_ICHORCNA
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            constants.CONSENSUS_FILE,
            constants.WF_CONSENSUS
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            constants.CONSENSUS_NORMAL_FILE,
            constants.WF_CONSENSUS_NORMAL
        )

        if wrapper.my_param_is_null(constants.RAW_COVERAGE):
            qc_dict = self.fetch_coverage_etl_data(config[self.identifier][constants.GROUP_ID])
            wrapper.set_my_param(constants.RAW_COVERAGE, qc_dict[constants.RAW_COVERAGE])

        # Get values for collapsed coverage for Pl and BC and put in config for QC reporting
        if wrapper.my_param_is_null(constants.COVERAGE_PL):
            wrapper.set_my_param(constants.COVERAGE_PL, self.process_consensus_cruncher(config[self.identifier][constants.CONSENSUS_FILE]))
        if wrapper.my_param_is_null(constants.COVERAGE_BC):
            wrapper.set_my_param(constants.COVERAGE_BC, self.process_consensus_cruncher(config[self.identifier][constants.CONSENSUS_NORMAL_FILE]))
        
        return wrapper.get_config()
    
    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        work_dir = self.workspace.get_work_dir()

        # Get purity and write it to purity.txt
        ichorcna_metrics_file = config[self.identifier][constants.ICHORCNA_FILE]
        ichor_json = self.process_ichor_json(ichorcna_metrics_file)
        self.workspace.write_json('ichor_metrics.json', ichor_json)
        purity = ichor_json["tumor_fraction"]
        self.write_purity(purity, work_dir)

        # If purity is <10%, only report as <10% (not exact number)
        purity = float(purity)
        rounded_purity = round(purity*100, 1)
        print(rounded_purity)
        if rounded_purity < 10:
            rounded_purity = "<10"

        results =  {
                constants.ONCOTREE: config[self.identifier][constants.ONCOTREE],
                constants.KNOWN_VARIANTS : config[self.identifier][constants.KNOWN_VARIANTS],
                constants.SAMPLE_TYPE : config[self.identifier][constants.SAMPLE_TYPE],
                constants.CANCER_CONTENT : rounded_purity,
                constants.RAW_COVERAGE : int(config[self.identifier][constants.RAW_COVERAGE]),
                constants.UNIQUE_COVERAGE : int(config[self.identifier][constants.COVERAGE_PL]),
            }
        data['results'] = results
        return data

    def fetch_coverage_etl_data(self, group_id):
        etl_cache = QCETLCache(self.QCETL_CACHE)
        cached_coverages = etl_cache.hsmetrics.metrics
        columns_of_interest = gsiqcetl.column.HsMetricsColumn
        data = cached_coverages.loc[ (cached_coverages[columns_of_interest.GroupID] == group_id),  [columns_of_interest.GroupID, columns_of_interest.MeanBaitCoverage] ]
        qc_dict = {}
        if len(data) > 0:
           qc_dict[constants.RAW_COVERAGE] = int(round(data.iloc[0][columns_of_interest.MeanBaitCoverage].item(),0))
        else:
            msg = "QC metrics associated with group_id {0} not found in QC-ETL and no value found in .ini ".format(group_id)
            raise MissingQCETLError(msg)
        return(qc_dict)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name('sample_template.html', data)

    def process_ichor_json(self, ichor_metrics):
        with open(ichor_metrics, 'r') as ichor_results:
            ichor_json = json.load(ichor_results)
        return(ichor_json)

    def process_consensus_cruncher(self, consensus_cruncher_file):
        header_line = False
        with open(consensus_cruncher_file, 'r') as cc_file:
            reader_file = csv.reader(cc_file, delimiter="\t")
            for row in reader_file:
                if row:
                    if row[0] == "BAIT_SET" :
                        header_line = True
                    elif header_line:
                        unique_coverage = float(row[9]) 
                        header_line = False
                    else:
                        next
        return(int(round(unique_coverage, 0)))

    def specify_params(self):
        discovered = [
            constants.GROUP_ID,
            constants.ONCOTREE,
            constants.KNOWN_VARIANTS,
            constants.SAMPLE_TYPE,
            constants.ICHORCNA_FILE,
            constants.RAW_COVERAGE,
            constants.CONSENSUS_FILE,
            constants.CONSENSUS_NORMAL_FILE,
            constants.COVERAGE_PL,
            constants.COVERAGE_BC
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        # Default parameters for priorities
        self.set_ini_default('configure_priority', 300)
        self.set_ini_default('extract_priority', 200)
        self.set_ini_default('render_priority', 500)

    def write_purity(self, purity, work_dir):
        """
        Writes the purity to a .txt file for other plugins to read.
        """
        out_path = os.path.join(work_dir, 'purity.txt')
        with open(out_path, "w") as file:
            file.write(str(purity))
        return out_path

class MissingQCETLError(Exception):
    pass 
