
import logging
import os
import pandas as pd
import random
import tempfile
import yaml
from djerba.components import dual_output_component
from djerba.utilities import constants
from djerba.utilities.tools import system_tools

class genetic_alteration(dual_output_component):
    """Base class; unit of genetic alteration data for cBioPortal"""

    # get_attributes_for_sample and get_genes are for demonstration only
    # will override in subclasses
    
    WORKFLOW_KEY = 'oicr_workflow'
    METADATA_KEY = 'metadata'
    INPUT_FILES_KEY = 'input_files'
    # additional metadata keys
    FILTER_VCF_KEY = 'filter_vcf'
    INPUT_DIRECTORY_KEY = 'input_directory'
    REGIONS_BED_KEY = 'regions_bed'
    
    def __init__(self, config, study_id, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.study_id = study_id
        # TODO shouldn't need to configure genetic_alteration_type and datatype
        # as these are fixed for each subclass
        try:
            self.genetic_alteration_type = config[constants.GENETIC_ALTERATION_TYPE_KEY]
            self.datatype = config[constants.DATATYPE_KEY]
            self.workflow = config[self.WORKFLOW_KEY]
            self.metadata = config[self.METADATA_KEY]
            self.input_files = config[self.INPUT_FILES_KEY]
            self.input_directory = self.metadata[self.INPUT_DIRECTORY_KEY]
        except KeyError as err:
            self.logger.error("Missing required config key: {0}".format(err))
            raise
        self.sample_ids = sorted(self.input_files.keys())
        self.sample_attributes = self.read_sample_attributes()
        # identifier for the genetic_alteration; should be unique in any given config
        self.alteration_id = "%s:%s" % (self.genetic_alteration_type, self.datatype)
        self.gene_names = None # used to cache the gene names

    def get_alteration_id(self):
        return self.alteration_id

    def get_attributes_for_sample(self, sample):
        """Get sample-level metrics for ShinyReport"""
        msg = "get_attributes_for_sample demo method of parent class; not intended for production"
        self.logger.warning(msg)
        metric_key = ":".join([self.genetic_alteration_type, self.datatype, 'dummy_sample_metric'])
        attributes = {
            metric_key: random.randrange(100)
        }
        return attributes

    def get_datatype(self):
        return self.datatype

    def get_genetic_alteration_type(self):
        return self.genetic_alteration_type

    def get_genes(self):
        """Placeholder; subclasses will read genes from input files"""
        msg = "get_genes demo method of parent class; not intended for production"
        self.logger.warning(msg)
        return ["Gene001", "Gene002"]

    def get_sample_ids(self):
        return self.sample_ids

    def get_small_mutation_indel_data(self, sample_id):
        """Get small mutation and indel data for ShinyReport"""
        msg = "get_small_mutation_indel_data demo method of parent class; not intended for production"
        self.logger.warning(msg)
        input_file = self.input_files[sample_id]
        # generate dummy results as a demonstration
        metric_key = ":".join([self.genetic_alteration_type, self.datatype, 'dummy_metric'])
        data = []
        for gene in self.get_genes():
            data.append(
                {
                    "Gene": gene,
                    metric_key: random.randrange(101, 1000)
                }
            )
        return data

    def read_sample_attributes(self):
        """Placeholder; read self.input_files and populate a sample attributes dictionary"""
        return {}


class mutation_extended(genetic_alteration):
    """
    Represents the MUTATION_EXTENDED genetic alteration type in cBioPortal.
    Generates reports for either cBioPortal or ShinyReport.
    """

    DATA_FILENAME = 'data_mutation_extended.maf'
    META_FILENAME = 'meta_mutation_extended.txt'

    def find_tmb(self):
        pass

    def get_attributes_for_sample(self, sample_id):
        # TODO compute and return sample-level metrics
        # TODO use self.REGIONS_BED_KEY and the prototype TMB function to compute the metric
        return {}
    
    def get_genes(self):
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

    def write_data(self, out_dir):
        """Write mutation data table for cBioPortal"""

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
        """Write mutation metadata for cBioPortal"""
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
