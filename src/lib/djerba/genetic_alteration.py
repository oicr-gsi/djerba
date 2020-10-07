
import logging
import os
import pandas as pd
import random
import tempfile
import yaml
from djerba.components import dual_output_component
from djerba.metrics import mutation_extended_metrics
from djerba.utilities import constants
from djerba.utilities.base import base
from djerba.utilities.tools import system_tools

class genetic_alteration(dual_output_component):
    """Base class; unit of genetic alteration data for cBioPortal and other reports"""

    # TODO in some instances, could write cBioPortal data to a tempdir and then extract elba metrics
    # The 'elba' methods get_attributes_for_sample and get_metrics_by_gene should be consistent
    # and avoid duplication with cBioPortal write_metrics
    
    WORKFLOW_KEY = 'oicr_workflow'
    METADATA_KEY = 'metadata'
    INPUT_FILES_KEY = 'input_files'
    # additional metadata keys
    FILTER_VCF_KEY = 'filter_vcf'
    INPUT_DIRECTORY_KEY = 'input_directory'
    REGIONS_BED_KEY = 'regions_bed'
    
    def __init__(self, config, study_id=None, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.study_id = study_id # required for cBioPortal, not for Elba
        try:
            self.genetic_alteration_type = config[constants.GENETIC_ALTERATION_TYPE_KEY]
            self.datatype = config[constants.DATATYPE_KEY]
            #self.workflow = config[self.WORKFLOW_KEY] # TODO is this field necessary?
            self.metadata = config[self.METADATA_KEY]
            self.input_files = config[self.INPUT_FILES_KEY]
            self.input_directory = self.metadata[self.INPUT_DIRECTORY_KEY]
        except KeyError as err:
            self.logger.error("Missing required config key: {0}".format(err))
            raise
        self.sample_ids = sorted(self.input_files.keys())
        self.sample_attributes = self._find_all_sample_attributes()
        # identifier for the genetic_alteration; should be unique in any given config
        self.alteration_id = "%s:%s" % (self.genetic_alteration_type, self.datatype)
        self.gene_names = None # used to cache the gene names

    def _find_all_sample_attributes(self):
        """PLACEHOLDER. Read self.input_files and populate a sample attributes dictionary"""
        msg = "_find_all_sample_attributes method of parent class; not intended for production"
        self.logger.error(msg)
        attributes = {}
        for sample_id in self.sample_ids:
            attributes[sample_id] = {}
        return attributes

    def get_alteration_id(self):
        """ID defined as 'alteration_type:datatype', eg. 'MUTATION_EXTENDED:MAF'"""
        return self.alteration_id

    def get_attributes_for_sample(self, sample_id):
        """Find attributes for given sample_id."""
        return self.sample_attributes[sample_id]

    def get_datatype(self):
        return self.datatype

    def get_genetic_alteration_type(self):
        return self.genetic_alteration_type

    def get_gene_names(self):
        """PLACEHOLDER. Get a list of gene names from the input files."""
        msg = "get_genes method of parent class; not intended for production"
        self.logger.error(msg)
        return []

    def get_metrics_by_gene(self, sample_id):
        """PLACEHOLDER. Get a dictionary of metric values for the given sample, indexed by gene."""
        msg = "get_metrics_by_gene method of parent class; not intended for production"
        self.logger.error(msg)
        return {}

    def get_sample_ids(self):
        return self.sample_ids


class genetic_alteration_factory(base):
    """Supply an instance of the appropriate genetic_alteration subclass for an ALTERATIONTYPE"""

    CLASSNAMES = {
        constants.DEMONSTRATION_TYPE: 'genetic_alteration_demo',
        constants.MUTATION_TYPE: 'mutation_extended'
    }

    def __init__(self, log_level=logging.WARN, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)

    def create_instance(self, config, study_id=None):
        """Return an instance of the genetic_alteration class named in the config"""
        alteration_type = config.get(constants.GENETIC_ALTERATION_TYPE_KEY)
        classname = self.CLASSNAMES.get(alteration_type)
        if alteration_type == None or classname == None:
            msg = "Unknown or missing %s value in config. " % constants.GENETIC_ALTERATION_TYPE_KEY
            msg = msg+" Permitted values are: %s" % str(sorted(list(self.CLASSNAMES.keys())))
            self.logger.error(msg)
            raise ValueError(msg)
        klass = globals().get(classname)
        return klass(config, study_id, self.log_level, self.log_path)


class genetic_alteration_demo(genetic_alteration):
    """Dummy class for demonstration and initial testing; not for production use"""

    def _find_all_sample_attributes(self):
        """DEMONSTRATION METHOD. Return empty attributes"""
        return {}

    def get_attributes_for_sample(self, sample_id):
        """DEMONSTRATION METHOD. Get sample-level metrics for Elba"""
        msg = "get_attributes_for_sample demo method; not intended for production"
        self.logger.warning(msg)
        metric_key = ":".join([self.genetic_alteration_type, self.datatype, 'dummy_sample_metric'])
        attributes = {
            metric_key: random.randrange(100)
        }
        return attributes

    def get_gene_names(self):
        """DEMONSTRATION METHOD. Get a list of gene names."""
        return ["Gene001", "Gene002"]

    def get_metrics_by_gene(self, sample_id):
        """"DEMONSTRATION METHOD. Get small mutation and indel data for Elba."""
        msg = "get_metrics_by_gene demo method; not intended for production"
        self.logger.warning(msg)
        input_file = self.input_files[sample_id]
        # generate dummy results as a demonstration
        metric_key = ":".join([self.alteration_id, 'dummy_metric'])
        metrics = {}
        for gene in self.get_gene_names():
            metrics[gene] = {
                constants.GENE_KEY: gene,
                metric_key: random.randrange(101, 1000)
            }
        return metrics


class mutation_extended(genetic_alteration):
    """
    Represents the MUTATION_EXTENDED genetic alteration type in cBioPortal.
    Generates reports for either cBioPortal or Elba.
    """

    DATA_FILENAME = 'data_mutation_extended.maf'
    META_FILENAME = 'meta_mutation_extended.txt'
    BED_PATH_KEY = 'bed_path'
    TCGA_PATH_KEY = 'tcga_path'
    CANCER_TYPE_KEY = 'cancer_type'

    def _find_all_sample_attributes(self):
        # TODO 'cancer_type' appears in study-level config. Could read it from there and
        # insert into the genetic_alteration config structure, instead of having duplicate
        # values in the study-level JSON config.
        try:
            bed_path = self.metadata[self.BED_PATH_KEY]
            tcga_path = self.metadata[self.TCGA_PATH_KEY]
            cancer_type = self.metadata[self.CANCER_TYPE_KEY]
        except KeyError as err:
            self.logger.error("Missing required metadata key: {0}".format(err))
            raise
        attributes = {}
        for sample_id in self.sample_ids:
            maf_path = self.input_files[sample_id]
            mx_metrics = mutation_extended_metrics(maf_path, bed_path, tcga_path, cancer_type)
            sample_attributes = {
                constants.TMB_PER_MB_KEY: mx_metrics.get_tmb()
            }
            attributes[sample_id] = sample_attributes
        return attirbutes
    
    def get_gene_names(self):
        """Find gene names from the input MAF files"""
        if self.gene_names:
            return self.gene_names
        gene_name_set = set()
        for input_file in self.input_files.values():
            # pandas read_csv() will automatically decompress .gz input
            df = pd.read_csv(os.path.join(self.input_directory, input_file))
            gene_name_set.update(set(df['Hugo_Symbol'].tolist()))
        # convert to list and sort
        gene_names = sorted(list(gene_name_set))
        self.gene_names = gene_names # store the gene names in case needed later
        return gene_names

    def get_metrics_by_gene(self, sample_id):
        """Return an empty data structure for now; TODO insert gene-level metrics"""
        metrics_by_gene = {}
        for name in self.get_gene_names():
            metrics_by_gene[gene] = {}
        return metrics_by_gene

    def write_data(self, out_dir):
        """cBioPortal. Write mutation data table."""

        # Read mutation data in MAF format and output in cBioPortal's required MAF format
        # May enable VCF input at a later date
        # see https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#mutation-data
        # required modules: vcf2maf/1.6.17, vep/92.0, vep-hg19-cache/92, hg19/p13

        tmp = tempfile.TemporaryDirectory(prefix='djerba_mutex_')
        tmp_dir = tmp.name
        #tmp_dir = '/scratch2/users/ibancarz/djerba_test/latest' # temporary location for testing
        input_paths = [os.path.join(self.input_directory, name) for name in self.input_files.values()]
        uncompressed = system_tools.decompress_gzip(input_paths, tmp_dir)
        commands = []
        output_paths = []
        for input_name in uncompressed:
            in_path = os.path.join(tmp_dir, input_name)
            out_path = os.path.join(tmp_dir, 'cbioportal.{}'.format(input_name))
            cmd = "maf2maf "+\
                  "--input-maf {} ".format(in_path)+\
                  "--output-maf {} ".format(out_path)+\
                  "--ref-fasta ${HG19_ROOT}/hg19_random.fa "+\
                  "--vep-path ${VEP_ROOT}/bin "+\
                  "--vep-data ${VEP_HG19_CACHE_ROOT}/.vep "+\
                  "--filter-vcf "+self.metadata.get(self.FILTER_VCF_KEY)
            commands.append(cmd)
            output_paths.append(out_path)
        # run the maf2maf commands
        system_tools.run_subprocesses(commands, self.logger)
        # concatenate the outputs by appending to a pandas DataFrame
        output_df = pd.read_csv(output_paths[0], delimiter="\t", comment="#")
        self.logger.debug("Read %s dataframe from %s" % (str(output_df.shape), output_paths[0]))
        for i in range(1, len(output_paths)):
            self.logger.debug("Appending %s dataframe from %s" % (str(output_df.shape), output_paths[i]))
            next_output = pd.read_csv(output_paths[i], delimiter="\t", comment="#")
            output_df = output_df.append(next_output)
        self.logger.debug("Dimensions of output dataframe are %s" % str(output_df.shape))
        out_path = os.path.join(out_dir, self.DATA_FILENAME)
        self.logger.info("Writing concatenated MAF output to %s" % out_path)
        output_df.to_csv(out_path, sep="\t")
        tmp.cleanup()
        
    def write_meta(self, out_dir):
        """cBioPortal. Write mutation metadata."""
        try:
            meta = {
                constants.STUDY_ID_KEY: self.study_id,
                constants.GENETIC_ALTERATION_TYPE_KEY: constants.MUTATION_TYPE,
                constants.DATATYPE_KEY: 'MAF',
                constants.STABLE_ID_KEY: 'mutations',
                constants.SHOW_PROFILE_IN_ANALYSIS_TAB_KEY: True,
                constants.PROFILE_NAME_KEY: self.metadata[constants.PROFILE_NAME_KEY],
                constants.PROFILE_DESCRIPTION_KEY: self.metadata[constants.PROFILE_DESCRIPTION_KEY],
                constants.DATA_FILENAME_KEY: self.DATA_FILENAME,
            }
            # omitting optional meta keys for now:
            # - gene_panel
            # - swissprot_identifier
            # - variant_classification_filter
            # - namespaces
        except KeyError as err:
            self.logger.error("Missing required config key: {0}".format(err))
            raise
        with open(os.path.join(out_dir, self.META_FILENAME), 'w') as out_file:
            out_file.write(yaml.dump(meta, sort_keys=True))
