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
        key_mapping = {k: k for k in keys}  # mapping from INI keys to input_params.json keys
        key_mapping[constants.GROUP_ID] = constants.TUMOUR_ID
        for key, val in key_mapping.items():
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

        # Have to extract purity here in order for purity to be supplied manually if needed
        # Purity needs to be supplied manually when making failed reports 

        ichorcna_file = wrapper.get_my_string(constants.ICHORCNA_FILE)
        purity = self.get_purity(wrapper, ichorcna_file)
        wrapper.set_my_param(constants.PURITY, purity)

        if wrapper.my_param_is_null(constants.RAW_COVERAGE):
            qc_dict = self.fetch_qc_etl_data(config[self.identifier][constants.GROUP_ID], constants.CACHE_COVERAGE, constants.RAW_COVERAGE)
            wrapper.set_my_param(constants.RAW_COVERAGE, qc_dict[constants.RAW_COVERAGE])

        if wrapper.my_param_is_null(constants.COVERAGE_PL):
            qc_dict = self.fetch_qc_etl_data(config[self.identifier][constants.GROUP_ID], constants.CACHE_COLLAPSED, constants.COVERAGE_PL)
            wrapper.set_my_param(constants.COVERAGE_PL, qc_dict[constants.COVERAGE_PL])

        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        work_dir = self.workspace.get_work_dir()

        # Processing of purity and writing purity to purity.txt
        purity = wrapper.get_my_string(constants.PURITY)
        
        if purity not in constants.ALLOWED_NA:
            try:
                # Round and clean purity for report aesthetic
                purity = float(purity)

            except ValueError:
                msg = f"Manually supplied purity should be one of {constants.ALLOWED_NA} or a float or integer."
                self.logger.error(msg)
                raise ValueError(msg)

            if not (0 <= purity <= 1):
                msg = f"Invalid purity value: {purity}. Must be between 0 and 1 (inclusive)."
                self.logger.error(msg)
                raise ValueError(msg)

            # If purity is <10%, only report as <10% (not exact number)
            purity = round(purity*100, 1)
            self.write_purity(purity, work_dir)
            if purity < 10:
                purity = "<10"

        # Account for other QCs being NA for failed reports 
        raw_coverage = config[self.identifier][constants.RAW_COVERAGE]
        collapsed_coverage = config[self.identifier][constants.COVERAGE_PL]
        if raw_coverage not in constants.ALLOWED_NA:
            try:
                raw_coverage = round(float(raw_coverage))
            except ValueError:
                msg = f"Manually supplied raw_coverage should be one of {constants.ALLOWED_NA} or a float or integer."
                self.logger.error(msg)
                raise ValueError(msg)
        if collapsed_coverage not in constants.ALLOWED_NA:
            try:
                collapsed_coverage = round(float(collapsed_coverage))
            except ValueError:
                msg = f"Manually supplied collapsed_coverage should be one of {constants.ALLOWED_NA} or a float or integer."
                self.logger.error(msg)
                raise ValueError(msg)

        results = {
            constants.ONCOTREE: config[self.identifier][constants.ONCOTREE],
            constants.KNOWN_VARIANTS: config[self.identifier][constants.KNOWN_VARIANTS],
            constants.SAMPLE_TYPE: config[self.identifier][constants.SAMPLE_TYPE],
            constants.CANCER_CONTENT: purity,
            constants.RAW_COVERAGE: raw_coverage,
            constants.UNIQUE_COVERAGE: collapsed_coverage,
        }
        data['results'] = results
        return data

    def get_cached_coverages(self, etl_cache, cache_name):
        return getattr(etl_cache, cache_name).metrics


    def get_purity(self, wrapper, ichorcna_path):
        # Get purity and write it to purity.txt
        ichorcna_path_exists = os.path.exists(ichorcna_path)
        
        if ichorcna_path_exists:
            if wrapper.my_param_is_not_null(constants.PURITY):
                msg = "Both a valid ichorcna file and purity were supplied. Prioritizing extraction of purity from the ichorcna file."
                self.logger.warning(msg)

            ichor_json = self.process_ichor_json(ichorcna_path)
            self.workspace.write_json('ichor_metrics.json', ichor_json)
            purity = ichor_json["tumor_fraction"]
            return purity

        elif not ichorcna_path_exists and wrapper.my_param_is_not_null(constants.PURITY):
            purity = wrapper.get_my_string(constants.PURITY)
            return purity

        elif not ichorcna_path_exists and wrapper.my_param_is_null(constants.PURITY):
            msg = "Both a valid ichorcna file and purity were not specified. If you have the ichorcna file, specify it so purity can be extracted. If not, set ichorcna_file=None and supply purity manually."
            self.logger.error(msg)
            raise ValueError(msg)


    def fetch_qc_etl_data(self, group_id, cache_name, qc_metric):
        etl_cache = QCETLCache(self.QCETL_CACHE)
        cached_coverages = self.get_cached_coverages(etl_cache, cache_name)
        columns_of_interest = gsiqcetl.column.HsMetricsColumn
        # Filter data for the group_id
        data = cached_coverages.loc[
            (cached_coverages[columns_of_interest.GroupID] == group_id),
            [
                columns_of_interest.GroupID,
                columns_of_interest.MeanBaitCoverage,
                columns_of_interest.TissueType,
            ]
        ]

        qc_dict = {}
        if len(data) > 0:
            # Exclude the reference
            filtered_data = data[data[columns_of_interest.TissueType] != 'R']

            if len(filtered_data) > 0:
                # Check if coverage values are unique
                coverage = filtered_data[columns_of_interest.MeanBaitCoverage].unique()
                if len(coverage) != 1:
                    msg = f"Multiple {qc_metric} values found for group_id {group_id}: {coverage}."
                    self.logger.error(msg)
                    raise ValueError(msg)
                else:
                    selected_value = coverage[0]
                    qc_dict[qc_metric] = int(round(selected_value, 0))
            else:
                msg = f"No valid {qc_metric} found for group_id {group_id} after filtering out the normal."
                self.logger.error(msg)
                raise MissingQCETLError(msg)
        else:
            msg = f"{qc_metric} associated with group_id {group_id} not found in QC-ETL and no value found in .ini."
            self.logger.error(msg)
            raise MissingQCETLError(msg)

        return qc_dict

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name('sample_template.html', data)

    def process_ichor_json(self, ichor_metrics):
        with open(ichor_metrics, 'r') as ichor_results:
            ichor_json = json.load(ichor_results)
        return ichor_json

    def process_consensus_cruncher(self, consensus_cruncher_file ):
        header_line = False
        with open(consensus_cruncher_file, 'r') as cc_file:
            reader_file = csv.reader(cc_file, delimiter="\t")
            for row in reader_file:
                if row:
                    if row[0] == "BAIT_SET":
                        header_line = True
                    elif header_line:
                        unique_coverage = float(row[9])
                        header_line = False
                    else:
                        next
        return int(round(unique_coverage, 0))

    def specify_params(self):
        discovered = [
            constants.GROUP_ID,
            constants.ONCOTREE,
            constants.KNOWN_VARIANTS,
            constants.SAMPLE_TYPE,
            constants.ICHORCNA_FILE,
            constants.RAW_COVERAGE,
            constants.COVERAGE_PL,
            constants.PURITY
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
