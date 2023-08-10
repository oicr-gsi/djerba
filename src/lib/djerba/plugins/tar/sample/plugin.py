"""
Djerba plugin for pwgs sample reporting
AUTHOR: Felix Beaudry
"""
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
from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer
import djerba.plugins.tar.provenance_tools as provenance_tools

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class main(plugin_base):

    PLUGIN_VERSION = '1.0.0'
    PRIORITY = 100
    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        group_id = config[self.identifier]['group_id']
        if wrapper.my_param_is_null('purity'):
            ichorcna_metrics_file = provenance_tools.subset_provenance(self, "ichorcna", group_id, "metrics\.json$")
            ichor_json = self.process_ichor_json(ichorcna_metrics_file) 
            self.workspace.write_json('ichor_metrics.json', ichor_json)
            purity = ichor_json["tumor_fraction"]
            wrapper.set_my_param('purity', float('%.1E' % Decimal(purity*100)))
        if wrapper.my_param_is_null('concensus_cruncher_file'):
            wrapper.set_my_param('concensus_cruncher_file', provenance_tools.subset_provenance(self, "consensusCruncher", group_id, "allUnique-hsMetrics\.HS\.txt$"))
        if wrapper.my_param_is_null('raw_coverage'):
            qc_dict = self.fetch_coverage_etl_data(group_id)
            wrapper.set_my_param('raw_coverage', qc_dict['raw_coverage'])
        return config
    
    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        unique_coverage = self.process_croncensus_cruncher(config[self.identifier]['concensus_cruncher_file'])
        results =  {
                "oncotree": config[self.identifier][constants.ONCOTREE],
                "known_variants" : config[self.identifier][constants.KNOWN_VARIANTS],
                "cancer_content" : float(config[self.identifier]['purity']),
                "raw_coverage" : int(config[self.identifier][constants.RAW_COVERAGE]),
                "unique_coverage" : unique_coverage,
                "files": {
                    "concensus_cruncher_file": config[self.identifier]['concensus_cruncher_file']
                }
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
           qc_dict['raw_coverage'] = int(round(data.iloc[0][columns_of_interest.MeanBaitCoverage].item(),0))
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

    def process_croncensus_cruncher(self, concensus_cruncher_file):
        header_line = False
        with open(concensus_cruncher_file, 'r') as cc_file:
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
        required = [
            'group_id',
            'oncotree',
            'known_variants'
        ]
        for key in required:
            self.add_ini_required(key)
        discovered = [
            'purity',
            'raw_coverage',
            'concensus_cruncher_file'
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

class MissingQCETLError(Exception):
    pass 
