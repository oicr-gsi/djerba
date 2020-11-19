"""Classes to handle Djerba configuration data"""

import json
import jsonschema
import logging
import os
import pandas as pd
from jsonschema.exceptions import ValidationError, SchemaError
from djerba.utilities.base import base
from djerba.utilities import constants


class builder(base):
    """Build a Djerba config data structure for Elba output"""
    
    INPUT_DIRECTORY_KEY = 'input_directory'
    INPUT_FILES_KEY = 'input_files'
    METADATA_KEY = 'metadata'
    # custom data
    GENE_HEADERS_KEY = 'gene_headers'
    GENE_TSV_KEY = 'gene_tsv'
    SAMPLE_HEADERS_KEY = 'sample_headers'
    SAMPLE_TSV_KEY = 'sample_tsv'
    # MAF data
    FILTER_VCF_KEY = 'filter_vcf'
    ONCOKB_TOKEN_KEY = 'oncokb_api_token'
    BED_PATH_KEY = 'bed_path'
    TCGA_PATH_KEY = 'tcga_path'
    CANCER_TYPE_KEY = 'cancer_type'

    def __init__(self, sample_id, log_level=logging.WARN, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.log_path = log_path
        self.sample_id = sample_id
    
    def build(self, custom_dir, gene_tsv, sample_tsv, maf, bed,
              cancer_type, oncokb_token, tgca, vcf, seg):
        """Build a config data structure from the given arguments"""
        config = {}
        samples = [
            {constants.SAMPLE_ID_KEY: self.sample_id}
        ]
        config[constants.SAMPLES_KEY] = samples
        genetic_alterations = []
        custom_config = self.build_custom(custom_dir, gene_tsv, sample_tsv)
        genetic_alterations.append(custom_config)
        mutex_config = self.build_mutex(maf, bed, cancer_type, oncokb_token, tgca, vcf)
        genetic_alterations.append(mutex_config)
        seg_config = self.build_segmented(seg)
        genetic_alterations.append(seg_config)
        config[constants.GENETIC_ALTERATIONS_KEY] = genetic_alterations
        self.logger.info("Djerba configuration complete; validating against schema")
        validator(self.logger.getEffectiveLevel(), self.log_path).validate(config, self.sample_id)
        return config

    def build_custom(self, custom_dir, gene_tsv, sample_tsv):
        """Create a data structure for CUSTOM_ANNOTATION config"""
        # read gene/sample headers from the TSV files; link from a temporary directory if needed
        gene_headers = self.read_tsv_headers(os.path.join(custom_dir, gene_tsv))
        sample_headers = self.read_tsv_headers(os.path.join(custom_dir, sample_tsv))
        config = {
            self.INPUT_DIRECTORY_KEY: custom_dir,
            self.INPUT_FILES_KEY: {}, # always empty for this datatype
            constants.DATATYPE_KEY: constants.CUSTOM_DATATYPE,
            constants.GENETIC_ALTERATION_TYPE_KEY: constants.CUSTOM_ANNOTATION_TYPE,
            self.METADATA_KEY: {
                self.GENE_HEADERS_KEY: gene_headers,
                self.GENE_TSV_KEY: gene_tsv,
                self.SAMPLE_HEADERS_KEY: sample_headers,
                self.SAMPLE_TSV_KEY: sample_tsv
            }
        }
        return config

    def build_mutex(self, maf, bed, cancer_type, oncokb_token, tcga, vcf):
        """Create a data structure for MUTATION_EXTENDED config"""
        [maf_dir, maf_file] = os.path.split(maf)
        config = {
            constants.DATATYPE_KEY: constants.MAF_DATATYPE,
            constants.GENETIC_ALTERATION_TYPE_KEY: constants.MUTATION_TYPE,
            self.INPUT_DIRECTORY_KEY: maf_dir,
            self.INPUT_FILES_KEY: {
                self.sample_id: maf_file
            },
            self.METADATA_KEY: {
                self.BED_PATH_KEY: bed,
                self.CANCER_TYPE_KEY: cancer_type,
                self.ONCOKB_TOKEN_KEY: oncokb_token,
                self.TCGA_PATH_KEY: tcga,
                self.FILTER_VCF_KEY: vcf
            }
        }
        return config

    def build_segmented(self, seg):
        """Create a data structure for SEGMENTED config"""
        [seg_dir, seg_file] = os.path.split(seg)
        config = {
            constants.DATATYPE_KEY: constants.SEG_DATATYPE,
            constants.GENETIC_ALTERATION_TYPE_KEY: constants.SEGMENTED_TYPE,
            self.INPUT_DIRECTORY_KEY: seg_dir,
            self.INPUT_FILES_KEY: {
                self.sample_id: seg_file
            },
            self.METADATA_KEY: {}
        }
        return config

    def read_tsv_headers(self, input_path):
        """Read a list of headers from a TSV file"""
        df = pd.read_csv(input_path, delimiter="\t", index_col=False)
        return list(df.columns.values)

class validator(base):

    """Validate Djerba config files against a JSON schema"""

    SCHEMA_FILENAME = 'input_schema.json'
    
    def __init__(self, log_level=logging.WARN, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        schema_path = os.path.join(
            os.path.dirname(__file__),
            constants.DATA_DIRNAME,
            self.SCHEMA_FILENAME
        )
        with open(schema_path, 'r') as schema_file:
            self.schema = json.loads(schema_file.read())

    def validate(self, config, sample_name):
        """Check the config data structure against the schema"""
        try:
            jsonschema.validate(config, self.schema)
            self.logger.debug("Djerba config is valid with respect to schema")
        except (ValidationError, SchemaError) as err:
            msg = "Djerba config is invalid with respect to schema"
            self.logger.error("{}: {}".format(msg, err))
            raise DjerbaConfigError(msg) from err
        if sample_name != None:
            sample_name_found = False
            for sample in config[constants.SAMPLES_KEY]:
                if sample[constants.SAMPLE_ID_KEY] == sample_name:
                    sample_name_found = True
                    self.logger.debug(
                        "Required sample name '{}' found in Djerba config".format(sample_name)
                    )
                    break
            if not sample_name_found:
                msg = "Required sample name '{}' not found in config".format(sample_name)
                self.logger.error(msg)
                raise DjerbaConfigError(msg)
        else:
            self.logger.debug("No sample name supplied, omitting check")
        self.logger.info("Djerba config is valid")
        return True

class DjerbaConfigError(Exception):
    pass
