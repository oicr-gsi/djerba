import os
import csv
import logging
import json
from decimal import Decimal

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.sample.constants as constants
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer
from djerba.plugins.tar.provenance_tools import subset_provenance_sample as subset_p_s
import djerba.util.input_params_tools as input_params_tools
from djerba.sequenza import sequenza_reader, SequenzaError

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError as err:
    raise RuntimeError('QC-ETL import failure! Try checking python versions') from err

class main(plugin_base):

    PLUGIN_VERSION = '1.0.0'
    PRIORITY = 200
    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"
    ETL_CACHE = QCETLCache(QCETL_CACHE)

    # Parameters
    ONCOTREE = "oncotree_code"
    SAMPLE_TYPE = "sample_type"
    TUMOUR_ID = "tumour_id"
    CALLABILITY = "callability"
    COVERAGE = "mean_coverage"
    PURITY = "cancer_cell_content"
    PLOIDY = "ploidy"
    SEQ_GAMMA = 'sequenza_gamma'
    SEQ_SOL = 'sequenza_solution'
    SEQ_FILE = 'sequenza_file'


    def specify_params(self):
        discovered = [
            self.ONCOTREE,
            self.SAMPLE_TYPE,
            self.SEQ_GAMMA,
            self.SEQ_SOL,

            self.CALLABILITY,
            self.COVERAGE,
            self.PURITY,
            self.PLOIDY,
            self.SEQ_FILE,
            self.TUMOUR_ID
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        
        # Get input_data.json if it exists; else return None
        input_data = input_params_tools.get_input_params_json(self)
        if input_data == None:
            msg = "Input_params.json does not exist. Parameters must be set manually."
            self.logger.warning(msg)

        # FIRST PASS: Get the input parameters
        if wrapper.my_param_is_null(self.ONCOTREE):
            wrapper.set_my_param(self.ONCOTREE, input_data[self.ONCOTREE])
        if wrapper.my_param_is_null(self.SAMPLE_TYPE):
            wrapper.set_my_param(self.SAMPLE_TYPE, input_data[self.SAMPLE_TYPE])
        if wrapper.my_param_is_null(self.SEQ_GAMMA):
            wrapper.set_my_param(self.SEQ_GAMMA, input_data[self.SEQ_GAMMA])
        if wrapper.my_param_is_null(self.SEQ_SOL):
            wrapper.set_my_param(self.SEQ_SOL, input_data[self.SEQ_SOL])

        # SECOND PASS: Get files based on input parameters

        # From sample info:
        # !!!!!!!!!!!!!! GET TUMOUR_ID FROM SAMPLE_INFO.JSON !!!!!!!!!!!!!!!
        if wrapper.my_param_is_null(core_constants.DEFAULT_SAMPLE_INFO) and assay != "TAR":
            wrapper.set_my_param(core_constants.DEFAULT_SAMPLE_INFO, os.path.join(work_dir, core_constants.DEFAULT_SAMPLE_INFO))
            info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
        tumour_id = info[self.TUMOUR_ID]

        if wrapper.my_param_is_null(self.CALLABILITY):
            wrapper.set_my_param(self.CALLABILITY, fetch_callability_etl_data(tumour_id))        
        if wrapper.my_param_is_null(self.COVERAGE):
            wrapper.set_my_param(self.COVERAGE, fetch_coverage_etl_data(tumour_id))
        
        seq_gamma = config[self.identifier][self.SEQ_GAMMA]
        seq_sol = config[self.identifier][self.SEQ_SOL]
        if wrapper.my_param_is_null(self.SEQ_FILE):
            wrapper.set_my_param(self.SEQ_SOL, #!!!!!!!!!!!!!!!!!!!!!!!!!)


        # Get purity and ploidy from sequenza file 

        reader = sequenza_reader(config[self.identifier][self.SEQ_FILE])
        gamma = config[self.identifier][self.SEQ_GAMMA]
        solution = config[self.identifier][self.SEQ_SOL]

        # get_default_gamma_id() returns (gamma, solution)
        if gamma == None:
            gamma = reader.get_default_gamma_id()[0]
            self.logger.info("Automatically generated Sequenza gamma: {0}".format(gamma))
        else:
            self.logger.info("User-supplied Sequenza gamma: {0}".format(gamma))
        if solution == None:
            solution = constants.SEQUENZA_PRIMARY_SOLUTION
            self.logger.info("Alternate Sequenza solution not supplied, defaulting to primary")
        try:
            purity = reader.get_purity(gamma, solution)
            ploidy = reader.get_ploidy(gamma, solution)
        except SequenzaError as err:
            msg = "Unable to find Sequenza purity/ploidy: {0}".format(err)
            self.logger.error(msg)
            raise
        self.logger.info("Sequenza purity {0}, ploidy {1}".format(purity, ploidy))


        return wrapper.get_config()
    
    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        work_dir = self.workspace.get_work_dir()

        
        # Configure with QC-ETL and Pinery: mean coverage, target coverage, callability.
        # Requires tumour and requisition IDs from discover_primary()
        tumour_id = self.config[ini.DISCOVERED][ini.TUMOUR_ID]
        qc_retriever = pull_qc(self.config)
        if self.config.has_option(ini.DISCOVERED, ini.MEAN_COVERAGE):
            msg = "Using manually configured mean coverage: {0}".format(self.config[ini.DISCOVERED][ini.MEAN_COVERAGE])
            self.logger.info(msg)
        else:
            try:
                coverage = qc_retriever.fetch_coverage_etl_data(tumour_id)
            except MissingQCETLError as e:
                msg = "Coverage not supplied by user, and cannot be retrieved from QC-ETL for tumour_id {0}: {1}".format(tumour_id, e)
                self.logger.error(msg)
                raise
            self.logger.info("Using mean coverage from QC-ETL: {0}".format(coverage))
            updates[ini.MEAN_COVERAGE] = coverage
        if self.config.has_option(ini.DISCOVERED, ini.PCT_V7_ABOVE_80X):
            msg = "Using manually configured callability: {0}".format(self.config[ini.DISCOVERED][ini.PCT_V7_ABOVE_80X])
            self.logger.info(msg)
        else:
            try:
                callability = qc_retriever.fetch_callability_etl_data(tumour_id)
            except MissingQCETLError as e:
                msg = "Callability not supplied by user, and cannot be retrieved from QC-ETL for tumour_id {0}: {1}".format(tumour_id, e)
                self.logger.error(msg)
                raise
            self.logger.info("Using callability from QC-ETL: {0}".format(coverage))
            updates[ini.PCT_V7_ABOVE_80X] = callability
        if self.config.has_option(ini.DISCOVERED, ini.TARGET_COVERAGE):
            msg = "Using manually configured target coverage: {0}".format(self.config[ini.DISCOVERED][ini.TARGET_COVERAGE])
            self.logger.info(msg)
        else:
            req_id = self.config[ini.INPUTS][ini.REQ_ID]
            try:
                target_coverage = qc_retriever.fetch_pinery_assay(req_id)
            except (MissingPineryError, UnsupportedAssayError) as e:
                msg = "Target coverage not supplied by user, and cannot be retrieved from Pinery for requisition ID {0}: {1}".format(req_id, e)
                self.logger.error(msg)
                raise
            self.logger.info("Using target coverage from Pinery: {0}".format(target_coverage))
            updates[ini.TARGET_COVERAGE] = target_coverage
        return updates


        results =  {
                "oncotree_code": config[self.identifier]['oncotree_code'],
                "known_variants" : config[self.identifier][constants.KNOWN_VARIANTS],
                "cancer_content" : rounded_purity,
                "raw_coverage" : int(config[self.identifier][constants.RAW_COVERAGE]),
                "unique_coverage" : int(config[self.identifier][constants.COLLAPSED_COVERAGE_PL]),
                "files": {
                    "consensus_cruncher_file": config[self.identifier]['consensus_cruncher_file'],
                    "ichorcna_file": config[self.identifier]['ichorcna_file']
                }
            }
        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name('sample_template.html', data)

    def fetch_callability_etl_data(self,tumour_id):
        cached_callabilities = self.ETL_CACHE.mutectcallability.mutectcallability
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
            self.logger.debug(msg)
            raise MissingQCETLError(msg)
        
    def fetch_coverage_etl_data(self,tumour_id):
        cached_coverages = self.ETL_CACHE.bamqc4merged.bamqc4merged
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


class MissingQCETLError(Exception):
    pass 
