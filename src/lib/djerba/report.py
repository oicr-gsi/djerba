import json
import logging
import os
import sys
from djerba.genetic_alteration import genetic_alteration
from djerba.sample import sample
from djerba.utilities import constants
from djerba.utilities.base import base


class report(base):

    """Class representing a genome interpretation Clinical Report"""

    def __init__(self, config, sample_id=None, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        study_id = config[constants.STUDY_META_KEY][constants.STUDY_ID_KEY]
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
        ga_key = constants.GENETIC_ALTERATIONS_KEY
        self.alterations = [
            genetic_alteration(ga_conf, study_id, log_level) for ga_conf in config[ga_key]
        ]
        report_sample = None

    def get_report_config(self):
        """Construct the reporting config data structure"""
        config = {}
        config[constants.GENOMIC_LANDSCAPE_KEY] = {}
        smi_results_by_gene = {} # small mutations and indels
        # for each genetic alteration, find values for smallMutAndIndel (if any) and update
        for alteration in self.alterations:
            # find small mutation and indel data
            smi_data = alteration.get_small_mutation_indel_data(self.sample_id)
            for gene_result in smi_data:
                gene_name = gene_result[constants.GENE_KEY]
                if gene_name in smi_results_by_gene:
                    smi_results_by_gene[gene_name].update(gene_result)
                else:
                    smi_results_by_gene[gene_name] = gene_result
            self.sample.update_attributes(alteration.get_attributes_for_sample(self.sample_id))
        # sort the results by gene name
        smi_sorted = [smi_results_by_gene[k] for k in sorted(smi_results_by_gene.keys())]
        config[constants.GENOMIC_LANDSCAPE_KEY][constants.SMALL_MUTATION_INDEL_KEY] = smi_sorted
        config[constants.CLINICAL_DATA_KEY] = self.sample.get_attributes()
        # TODO add other parts of the "genomic landscape", eg. oncoKB SVs & CNVs
        # TODO add other elements of report JSON, eg. "SVandFus", "exprOutliers"
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
