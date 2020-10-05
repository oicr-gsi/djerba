"""Class to represent a study directory, formatted for upload to cBioPortal"""

import json
import logging
import os
from shutil import rmtree

from djerba.components import cancer_type, case_list, study_meta, patients_component, samples_component
from djerba.genetic_alteration import genetic_alteration, mutation_extended
from djerba.sample import sample
from djerba.utilities.base import base
from djerba.utilities import constants

class study(base):

    # TODO move these cBioPortal constants into the shared module
    CNA_TYPE = 'COPY_NUMBER_ALTERATION'
    EXPRESSION_TYPE = 'MRNA_EXPRESSION'
    MUTATION_TYPE = 'MUTATION_EXTENDED'
    DISCRETE_DATATYPE = 'DISCRETE'

    CANCER_TYPE_KEY = 'cancer_type'
    CASE_LISTS_KEY = 'case_lists'
    GENETIC_ALTERATIONS_KEY = 'genetic_alterations'
    SAMPLES_KEY = 'samples'
    SAMPLES_META_KEY = 'samples_meta'
    STUDY_META_KEY = 'study_meta'
    TYPE_OF_CANCER_KEY = 'type_of_cancer'
    WRITE_PATIENTS_KEY = 'write_patients'

    # 'cancer type' and 'type of cancer' are distinct terms in cBioPortal.
    # Respectively, they are an output file format, and a string in study metadata
    
    def __init__(self, config, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        study_meta_config = config.get(self.STUDY_META_KEY)
        self.study_meta = study_meta(study_meta_config)
        self.study_id = study_meta_config.get(constants.STUDY_ID_KEY)
        type_of_cancer_string = study_meta_config.get(self.TYPE_OF_CANCER_KEY)
        if config.get(self.CANCER_TYPE_KEY):
            self.cancer_type = cancer_type(
                config.get(self.CANCER_TYPE_KEY), type_of_cancer_string, log_level=log_level
            )
        else:
            self.cancer_type = None
        # read sample info
        self.samples = []
        sample_id_set = set()
        for sample_json in config.get(self.SAMPLES_KEY):
            sample_object = sample(sample_json)
            self.samples.append(sample_object)
            sample_id_set.add(sample_object.get_id())
        # TODO allow patient/sample output to be configured independently
        # for now, we are using the same config for both; technically correct, but inflexible
        clinical_data = self.get_clinical_data(config.get(self.SAMPLES_META_KEY))
        [self.sample_component, self.patient_component] = clinical_data
        self.genetic_alterations = []
        self.ga_ids = set()
        # find genetic alterations and check study-wide consistency
        for ga_config in config.get(self.GENETIC_ALTERATIONS_KEY):
            if ga_config[constants.GENETIC_ALTERATION_TYPE_KEY] == constants.MUTATION_TYPE:
                ga = mutation_extended(ga_config, self.study_id, log_level=log_level)
            else:
                # default case for testing
                # make an instance of the base class; should NOT be done in production
                self.logger.warning("Using base genetic_alteration class; NOT supported for production")
                ga = genetic_alteration(ga_config, self.study_id, log_level=log_level)
            # check uniqueness of genetic alteration id
            genetic_alt_id = ga.get_alteration_id()
            if genetic_alt_id in self.ga_ids:
                msg = "Non-unique (genetic_alteration_type, datatype) pair : %s" % genetic_alt_id
                self.logger.error(msg)
                raise ValueError(msg)
            else:
                self.ga_ids.add(genetic_alt_id)
            ga_sample_id_set = set(ga.get_sample_ids())
            # check samples are a subset of the study samples list
            if not ga_sample_id_set.issubset(sample_id_set):
                diff = ga_sample_id_set - sample_id_set
                msg = "Sample IDs for alteration %s:%s do not appear in study samples list: %s" \
                      % (ga.get_alteration_id(), ", ".join(diff))
                self.logger.error(msg)
                raise ValueError(msg)
            self.genetic_alterations.append(ga)
        # find case lists last, so we can refer to genetic_alteration setup
        self.case_lists = self.get_case_lists(config.get(self.CASE_LISTS_KEY))

    def check_output_dir(self, out_dir):
        """check if a directory is valid for writing output"""
        valid = True
        if not os.path.exists(out_dir):
            valid = False
            self.logger.error("Output directory %s does not exist" % out_dir)
        elif not os.path.isdir(out_dir):
            valid = False
            self.logger.error("Output path %s is not a directory" % out_dir)
        elif not os.access(out_dir, os.W_OK):
            valid = False
            self.logger.error("Output path %s is not writable" % out_dir)
        if not valid:
            msg = "Invalid output directory %s; exiting" % out_dir
            self.logger.error(msg)
            raise OSError(msg)
        if len(os.listdir(out_dir)) > 0:
            prefix = "Output directory %s is not empty; " % out_dir
            if force:
                self.logger.info(prefix+"--force is in effect, removing directory contents.")
                rmtree(out_dir)
                os.mkdir(out_dir)
            else:
                 msg = prefix+"exiting. Run with --force to delete contents of directory."
                 self.logger.error(msg)
                 raise OSError(msg)

    def get_case_lists(self, case_list_config):
        """Generate required and custom case lists"""
        case_lists = []
        for config in case_list_config: # custom case lists
            case_lists.append(case_list(self.study_id, config))
        cna_samples = set()
        mutation_samples = set()
        expression_samples = set()
        for ga in self.genetic_alterations:
            ga_type = ga.get_genetic_alteration_type()
            if ga_type == self.CNA_TYPE:
                cna_samples.update(set(ga.get_sample_ids()))
                if ga.get_datatype() == self.DISCRETE_DATATYPE:
                    config = { # case list required by cBioPortal
                        case_list.SUFFIX_KEY: "cna",
                        case_list.CASE_LIST_NAME_KEY: "CNA discrete",
                        case_list.CASE_LIST_DESCRIPTION_KEY: "Samples with discrete CNA data",
                        case_list.CASE_LIST_IDS_KEY: ga.get_sample_ids(),
                    }
                    case_lists.append(case_list(self.study_id, config))
            elif ga_type == self.MUTATION_TYPE:
                mutation_samples.update(set(ga.get_sample_ids()))
                config = {    # case list required by cBioPortal
                    case_list.SUFFIX_KEY: "sequenced",
                    case_list.CASE_LIST_NAME_KEY: "sequenced mutation data",
                    case_list.CASE_LIST_DESCRIPTION_KEY: "Samples with mutation data",
                    case_list.CASE_LIST_IDS_KEY: ga.get_sample_ids(),
                }
                case_lists.append(case_list(self.study_id, config))
            elif ga_type == self.EXPRESSION_TYPE:
                expression_samples.update(set(ga.get_sample_ids()))
        cnaseq_ids = cna_samples.intersection(mutation_samples)
        # automatically generate additional case lists of interest
        if len(cnaseq_ids) > 0:
            config =  {
                case_list.SUFFIX_KEY: "cnaseq",
                case_list.CASE_LIST_NAME_KEY: "Samples profiled for mutations and CNAs",
                case_list.CASE_LIST_DESCRIPTION_KEY: "Case list containing all samples profiled for mutations and CNAs",
                case_list.CASE_LIST_IDS_KEY: list(cnaseq_ids),
            }
            case_lists.append(case_list(self.study_id, config))
        triple_complete_ids = cna_samples.intersection(mutation_samples, expression_samples)
        if len(triple_complete_ids) > 0:
            config =  {
                case_list.SUFFIX_KEY: "3way_complete",
                case_list.CASE_LIST_NAME_KEY: "Samples profiled for mutations, CNAs, and mRNA expression",
                case_list.CASE_LIST_DESCRIPTION_KEY: "Case list containing all samples profiled for mutations, CNAs, and mRNA expression",
                case_list.CASE_LIST_IDS_KEY: list(triple_complete_ids),
            }
            case_lists.append(case_list(self.study_id, config))
        return case_lists

    def get_clinical_data(self, samples_meta):
        """Cross-reference samples with samples metadata to get clinical data components"""
        sc = samples_component(self.samples, samples_meta, self.study_id)
        if samples_meta.get(self.WRITE_PATIENTS_KEY):
            pc = patients_component(self.samples, samples_meta, self.study_id)
        else:
            pc = None
        return [sc, pc]

    def write_all(self, out_dir, dry_run=False, force=False):
        """Write all outputs to the given directory path"""
        self.check_output_dir(out_dir)
        self.study_meta.write(out_dir)
        self.sample_component.write(out_dir)
        if self.cancer_type:
            self.cancer_type.write(out_dir)
        if self.patient_component:
            self.patient_component.write(out_dir)
        case_list_dir = os.path.join(out_dir, 'case_lists')
        if len(self.case_lists) > 0:
            if os.path.exists(case_list_dir):
                self.check_output_dir(case_list_dir)
            else:
                os.makedirs(case_list_dir)
            for case_list in self.case_lists:
                case_list.write(case_list_dir)
        for genetic_alteration in self.genetic_alterations:
            if dry_run:
                ga_id = genetic_alteration.get_alteration_id()
                msg = "Dry-run mode; omitting output for genetic alteration %s" % ga_id
                self.logger.warning(msg)
            else:
                genetic_alteration.write(out_dir)


