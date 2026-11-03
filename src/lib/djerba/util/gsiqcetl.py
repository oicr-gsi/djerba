"""Code to support the GSI QC-ETL cache"""

import math
import os
from importlib import import_module
from importlib.util import find_spec
from djerba.plugins.base import plugin_base
from djerba.util.environment import directory_finder, DjerbaEnvDirError
from djerba.util.validator import path_validator


class gsiqcetl_plugin_base(plugin_base):

    """Plugin base class which supports queries to the GSI QC-ETL cache.
    The cache classes are internal to OICR, and not available to external users,
    so loading is done specially and failure to load is not a fatal error.
    """

    # QCETL_CACHE_DEFAULT = "/scratch2/groups/gsi/production/qcetl_v1"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gsiqcetl_OK = False # True if library and cache dir are both available
        # check for the gsiqcetl Python library
        if find_spec('gsiqcetl')==None:
            # gsiqcetl Python package is not on the PYTHONPATH
            warning = "GSI-QC-ETL API not found: Coverage and callability must "+\
                "be specified manually in the INI file. (The GSI-QC-ETL cache and "+\
                "associated Python package are "+\
                "internal to OICR and not available externally.)"
            self.logger.warn(warning)
            self.gsiqcetl_column = None
            self.QCETLCache = None
        else:
            try:
                # Import the required classes/modules and assign to instance variables.
                # We do it this way because for a simple 'import' statement,
                # the imported names are in scope for the local context only.
                # So inside a function like this, 'import' does not
                # make the names available to the rest of the plugin.
                self.gsiqcetl_column = import_module('gsiqcetl.column')
                self.QCETLCache = import_module('gsiqcetl.api').QCETLCache
            except ImportError as err:
                msg = 'QC-ETL import failure! Try checking python versions'
                raise RuntimeError(msg) from err
            # now check the cache directory
            finder = directory_finder(strict=False)
            self.gsiqcetl_cache_dir = finder.get_gsiqcetl_cache_dir()
            if self.gsiqcetl_cache_dir == None:
                self.logger.warn("GSI-QC-ETL cache directory is not available")
            else:
                self.gsiqcetl_OK = True
                
    def gsiqcetl_ok(self):
        return self.gsiqcetl_OK

    def get_qcetl_cache(self):
        if not self.gsiqcetl_ok():
            msg = "Attempted to get QC-ETL cache, but it is not available"
            self.logger.error(msg)
            raise RuntimeError(msg)
        etl_cache = self.QCETLCache(self.gsiqcetl_cache_dir)
        return etl_cache

    def fetch_callability_etl_data(self, etl_cache, donor, tumour_id, ignore_warning):
        """
        Fetch callability for the WGTS sample plugin and check against minimum threshold
        """
        msg = "Fetching callability from GSI-QC-ETL for "+\
            f"donor {donor}, tumour ID {tumour_id}"
        self.logger.debug(msg)
        cached_callabilities = etl_cache.mutectcallability.mutectcallability
        columns_of_interest = self.gsiqcetl_column.MutetctCallabilityColumn
        metric_column = columns_of_interest.Callability
        data = self.filter_by_donor_and_tumour_id(donor, tumour_id, cached_callabilities, columns_of_interest, metric_column)
        if len(data) == 1:
            # Round down to one decimal place
            callability = math.floor(data.iloc[0][columns_of_interest.Callability].item() * 1000) / 10
            callability_threshold = 75
            if callability < callability_threshold and not ignore_warning:
                msg = f"Callability is below the reportable threshold: {callability:.1f}% < {callability_threshold}%. This may be overridden at the user's discretion by setting ignore_warning=True."
                self.logger.error(msg)
                raise LowCallabilityError(msg)
            self.logger.debug("Found callability: {0}".format(callability))
            return callability
        elif len(data) > 1:
            msg = "Djerba found more than one callability associated with donor {0} and tumour_id {1} in QC-ETL. Double check that the callability found by Djerba is correct; if not, may have to manually specify the callability.".format(donor, tumour_id)
            self.logger.warning(msg)
        else:
            msg = "Djerba couldn't find the callability associated with donor {0} and tumour_id {1} in QC-ETL.".format(donor, tumour_id)
            self.logger.error(msg)
            raise MissingQCETLError(msg)
        
    def fetch_coverage_etl_data(self, etl_cache, donor, tumour_id):
        """
        Fetch coverage for the WGTS sample plugin
        """
        self.logger.debug("Fetching coverage from GSI-QC-ETL for donor "+donor)
        cached_coverages = etl_cache.bamqc4merged.bamqc4merged
        columns_of_interest = self.gsiqcetl_column.BamQc4MergedColumn
        metric_column = columns_of_interest.CoverageDeduplicated
        data = self.filter_by_donor_and_tumour_id(donor, tumour_id, cached_coverages, columns_of_interest, metric_column)
        if len(data) == 1:
            coverage_value = round(data.iloc[0][columns_of_interest.CoverageDeduplicated].item(),1)
            self.logger.debug("Found coverage: {0}".format(coverage_value))
            return(coverage_value)
        elif len(data) > 1:
            msg = "Djerba found more than one coverage associated with donor {0} and tumour_id {1} in QC-ETL. Double check that the coverage found by Djerba is correct; if not, may have to manually specify the coverage.".format(donor, tumour_id)
            self.logger.warning(msg)

        else:
            msg = "Djerba couldn't find the coverage associated with donor {0} and tumour_id {1} in QC-ETL. ".format(donor, tumour_id)
            self.logger.debug(msg)
            raise MissingQCETLError(msg)

    def filter_by_donor_and_tumour_id(self, donor, tumour_id, cached_data, columns_of_interest, metric_column):
        # Note: donor and tumour ID are both not unique, but together are unique. Filter on both.
        # One donor can have multiple tumour IDs; one tumour ID can be associated with multiple donors
        # But one donor will not have a duplicate tumour IDs
        data = cached_data.loc[
            (cached_data[columns_of_interest.GroupID] == tumour_id) &
            (cached_data[columns_of_interest.Donor] == donor),
            [columns_of_interest.GroupID, columns_of_interest.Donor, metric_column]
        ]
        return data

    def fetch_tar_etl_data(self, group_id, cache_name, qc_metric):
        """
        QC-ETL fetch method used in the TAR sample plugin
        Has a filter to exclude normal data, and a mean bait coverage check
        """
        etl_cache = self.get_qcetl_cache()
        cached_coverages = self.get_cached_coverages(etl_cache, cache_name)
        columns_of_interest = self.gsiqcetl_column.HsMetricsColumn
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
        self.logger.debug("Fetched metrics from GSI-QC-ETL: {0}".format(qc_dict))
        return qc_dict


class MissingQCETLError(Exception):
    pass
