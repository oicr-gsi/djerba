"""Genome interpretation Clinical Report configuration"""

import json
import logging
import os
import sys
from djerba.genetic_alteration import genetic_alteration_factory
from djerba.sample import sample
from djerba.utilities import constants
from djerba.utilities.base import base


class report(base):

    """Class representing a genome interpretation Clinical Report in Elba"""

    def __init__(self, config, sample_id=None, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        study_id = config[constants.STUDY_META_KEY][constants.STUDY_ID_KEY]
        # configure the sample for the report
        if sample_id==None: # only one sample
            if len(config[constants.SAMPLES_KEY])==1:
                self.sample = sample(config[constants.SAMPLES_KEY][0], log_level)
                self.sample_id = self.sample.get_id()
            else:
                msg = "Config contains multiple samples; must specify which one to use in report"
                self.logger.error(msg)
                raise DjerbaReportError(msg)
        else: # multiple samples, see if the requested sample_id is present
            self.sample_id = sample_id
            report_sample = None
            for sample_config in config[constants.SAMPLES_KEY]:
                if sample_config[constants.SAMPLE_ID_KEY] == sample_id:
                    report_sample = sample(sample_config, log_level)
                    break
            if report_sample:
                self.sample = report_sample
            else:
                msg = "Could not find requested sample ID '%s' in config" % sample_id
                self.logger.error(msg)
                raise DjerbaReportError(msg)
        # populate the list of genetic alterations
        ga_factory = genetic_alteration_factory(log_level, log_path)
        ga_configs = config[constants.GENETIC_ALTERATIONS_KEY]
        self.alterations = [
            ga_factory.create_instance(conf, study_id) for conf in ga_configs
        ]

    def get_report_config(self):
        """Construct the reporting config data structure"""
        # for each genetic alteration, find metric values at sample/gene level
        all_metrics_by_gene = {}
        for alteration in self.alterations:
            # update gene-level metrics
            metrics_by_gene = alteration.get_metrics_by_gene(self.sample_id)
            for gene_id in metrics_by_gene.keys():
                if gene_id in all_metrics_by_gene:
                    all_metrics_by_gene[gene_id].update(metrics_by_gene[gene_id])
                else:
                    all_metrics_by_gene[gene_id] = metrics_by_gene[gene_id]
            # update sample-level metrics
            self.sample.update_attributes(alteration.get_attributes_for_sample(self.sample_id))
        # reorder gene-level metrics into a list
        gene_metrics_list = []
        for gene_id in all_metrics_by_gene.keys():
            metrics = all_metrics_by_gene[gene_id]
            metrics[constants.GENE_KEY] = gene_id
            gene_metrics_list.append(metrics)
        # assemble the config data structure
        config = {}
        config[constants.SAMPLE_INFO_KEY] = self.sample.get_attributes()
        config[constants.GENE_METRICS_KEY] = gene_metrics_list
        config[constants.REVIEW_STATUS_KEY] = -1 # placeholder; will be updated by Elba
        return config

    def write_report_config(self, out_path, force=False):
        if out_path=='-':
            out_file = sys.stdout
        else:
            if os.path.exists(out_path):
                if force:
                    msg = "--force mode in effect; overwriting existing output %s" % out_path
                    self.logger.info(msg)
                else:
                    msg = "Output %s already exists; exiting. Use --force mode to overwrite." % out_path
                    self.logger.error(msg)
                    raise DjerbaReportError(msg)
            out_file = open(out_path, 'w')
        out_file.write(json.dumps(self.get_report_config(), sort_keys=True, indent=4))
        if out_path!='-':
            out_file.close()

class DjerbaReportError(Exception):
    pass
