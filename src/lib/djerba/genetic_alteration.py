"""
Source of input data for Djerba; corresponds to the genetic_alteration_type metadata field in cBioPortal.

A `genetic_alteration` object reads input from files, database queries, etc.; parses sample-level and gene-level attributes; and returns them in standard data structures.

Includes:

- `genetic alteration`: Abstract base class
- Subclasses to implement genetic_alteration methods for particular data types
- `genetic_alteration_factory`: Class to construct an instance of an appropriate `genetic_alteration` subclass, given its name and other configuration data.
"""

import logging
import os
import pandas as pd
import random
import tempfile
import yaml
from djerba.metrics import mutation_extended_metrics
from djerba.utilities import constants
from djerba.utilities.base import base
from djerba.utilities.tools import system_tools

class genetic_alteration(base):
    """Base class; unit of genetic alteration data for cBioPortal and other reports"""

    # TODO make into a Python AbstractBaseClass: https://docs.python.org/3/library/abc.html

    # top-level config keys
    WORKFLOW_RUN_ID_KEY = 'workflow_run_id'
    METADATA_KEY = 'metadata'
    INPUT_FILES_KEY = 'input_files'
    INPUT_DIRECTORY_KEY = 'input_directory'
    # additional metadata keys
    FILTER_VCF_KEY = 'filter_vcf'
    REGIONS_BED_KEY = 'regions_bed'
    
    def __init__(self, config, study_id=None, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.study_id = study_id # required for cBioPortal, not for Elba
        try:
            self.genetic_alteration_type = config[constants.GENETIC_ALTERATION_TYPE_KEY]
            self.datatype = config[constants.DATATYPE_KEY]
            self.metadata = config[self.METADATA_KEY]
            self.input_files = config[self.INPUT_FILES_KEY]
            self.input_directory = config[self.INPUT_DIRECTORY_KEY]
        except KeyError as err:
            self.logger.error("Missing required config key: {0}".format(err))
            raise
        self.workflow_run_id = config.get(self.WORKFLOW_RUN_ID_KEY, None) # optional param
        self.sample_ids = self._get_sample_ids()
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

    def _get_sample_ids(self):
        """
        Find the list of sample IDs. Assumes the input_files config is non-empty.
        Optionally, can override this method in child classes.
        """
        return sorted(self.input_files.keys())

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
        """
        PLACEHOLDER. Get a list of gene names from the input files.
        Not run from __init__() because it can be quite slow (eg. reading multiple MAF files).
        """
        msg = "get_genes method of parent class; not intended for production"
        self.logger.error(msg)
        return []

    def get_input_path(self, sample_id):
        return os.path.join(self.input_directory, self.input_files[sample_id])
    
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
        constants.CUSTOM_ANNOTATION_TYPE: 'custom_annotation',
        constants.MUTATION_TYPE: 'mutation_extended',
        constants.SEGMENTED_TYPE: 'segmented'
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

class custom_annotation(genetic_alteration):
    """
    User-defined custom annotation supplied in TSV format.

    ## Input requirements

    - Input is in separate TSV files for gene and sample annotation.
    - Gene and sample filenames are specified in metadata, as 'gene_tsv' and 'sample_tsv' respectively.
    - Input files are tab-delimited, and may include comment lines starting with #.
    - Annotations which contain tab characters may be enclosed in double quotes (").
    - Column headers in the gene and sample files must be specified in config metadata, as 'gene_headers' and 'sample_headers' respectively.
    - The first column must be the gene or sample identifier, with header 'Gene' or 'SAMPLE_ID' respectively.
    - If column headers from metadata are not found in the TSV file, it will raise an error.
    - Columns in the TSV file which do not appear in metadata are silently ignored.

    ## Notes

    - Useful as a fallback for fields which cannot be automatically obtained by Djerba.
    - Currently supports Elba output only, not cBioPortal.
    """

    GENE_HEADERS_KEY = 'gene_headers'
    GENE_TSV_KEY = 'gene_tsv'
    SAMPLE_HEADERS_KEY = 'sample_headers'
    SAMPLE_TSV_KEY = 'sample_tsv'

    def _find_all_sample_attributes(self):
        """Read attributes for each sample from a TSV file with specified headers"""
        try:
            tsv_path = os.path.join(self.input_directory, self.metadata[self.SAMPLE_TSV_KEY])
            column_headers = self.metadata[self.SAMPLE_HEADERS_KEY] # must start with SAMPLE_ID_KEY
        except KeyError as err:
            self.logger.error("Missing required metadata key: {0}".format(err))
            raise
        if column_headers[0] != constants.SAMPLE_ID_KEY:
            msg = "First sample column header in metadata must be %s" % constants.SAMPLE_ID_KEY
            self.logger.error(msg)
            raise ValueError(msg)
        attributes = {}
        df = self._read_columns(tsv_path, column_headers, constants.SAMPLE_ID_KEY)
        keys = df.columns.values.tolist() # use df instead of column_headers, to preserve column order
        for (sample_id, row) in df.iterrows():
            # row.to_list() is a workaround for int64 conversion; see comments in get_metrics_by_gene
            values = row.to_list()
            attributes[sample_id] = {keys[i]: values[i] for i in range(len(values))}
        return attributes

    def _get_sample_ids(self):
        """Read sample IDs from TSV input file; overrides method of parent class"""
        try:
            tsv_path = os.path.join(self.input_directory, self.metadata[self.SAMPLE_TSV_KEY])
        except KeyError as err:
            self.logger.error("Missing required metadata key: {0}".format(err))
            raise
        df = self._read_columns(tsv_path, [constants.SAMPLE_ID_KEY], None, index_col=False)
        return df[constants.SAMPLE_ID_KEY].tolist()

    def _read_columns(self, input_path, column_headers, index_name, index_col=0):
        """
        Read specified columns from TSV into a Pandas DataFrame.
        Raise an error if any requested columns are missing; warn if any values are null.
        index_col is the parameter of the same name for Pandas read_csv().
        index_name is the expected name of the index column; must be None if index_col=False.
        """
        try:
            df = pd.read_csv(
                input_path,
                delimiter="\t",
                comment="#",
                index_col=index_col,
                usecols=column_headers
            )
        except ValueError as err:
            msg = 'Failed to read TSV from "{0}". Missing required column headers '.format(input_path) +\
                  'from Djerba config? Pandas error message: "{0}"'.format(err)
            self.logger.error(msg)
            raise
        if df.isnull().values.any():
            self.logger.info(
                'Null values in TSV data read from "{0}" '.format(input_path)+\
                'with column headers {0}'.format(str(column_headers))
            )
        if index_col is False and index_name!=None: # 0 has truth-value False, so use 'is' instead of '=='
            msg = "index_name must be None if index_col is False"
            self.logger.error(msg)
            raise ValueError(msg)
        elif df.index.name != index_name:
            msg = "First column header in %s: Expected %s, found %s" % \
                  (input_path, index_name, df.index.name)
            self.logger.error(msg)
            raise ValueError(msg)
        return df

    def get_gene_names(self):
        """Find gene names from TSV input file"""
        if self.gene_names:
            return self.gene_names
        try:
            tsv_path = os.path.join(self.input_directory, self.metadata[self.GENE_TSV_KEY])
        except KeyError as err:
            self.logger.error("Missing required metadata key: {0}".format(err))
            raise
        df = self._read_columns(tsv_path, [constants.GENE_KEY], None, index_col=False)
        return df[constants.GENE_KEY].tolist()

    def get_metrics_by_gene(self, sample_id):
        """Read gene-level metrics from input TSV."""
        try:
            tsv_path = os.path.join(self.input_directory, self.metadata[self.GENE_TSV_KEY])
            column_headers = self.metadata[self.GENE_HEADERS_KEY] # must start with GENE_KEY
        except KeyError as err:
            self.logger.error("Missing required metadata key: {0}".format(err))
            raise
        if column_headers[0] != constants.GENE_KEY:
            msg = "First gene column header in metadata must be %s" % constants.GENE_KEY
            self.logger.error(msg)
            raise ValueError(msg)
        metrics_by_gene = {}
        df = self._read_columns(tsv_path, column_headers, constants.GENE_KEY)
        for (gene_name, row) in df.iterrows():
            # Can't use row.get() because this may return an int64, which can't be serialized to JSON
            # row.to_list() converts all values to Python scalars, so can be used as a workaround
            # See https://bugs.python.org/issue24313
            values = row.to_list()
            metrics_by_gene[gene_name] = {column_headers[i+1]: values[i] for i in range(len(values))}
        return metrics_by_gene

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

    # MAF column headers
    HUGO_SYMBOL = 'Hugo_Symbol'
    CHROMOSOME = 'Chromosome'

    def _find_all_sample_attributes(self):
        # TODO 'cancer_type' appears in study-level config. Could read it from there and
        # insert into the genetic_alteration config structure, instead of having duplicate
        # values in the study-level JSON config.
        try:
            bed_path = os.path.join(self.input_directory, self.metadata[self.BED_PATH_KEY])
            tcga_path = os.path.join(self.input_directory, self.metadata[self.TCGA_PATH_KEY])
            cancer_type = self.metadata[self.CANCER_TYPE_KEY]
        except KeyError as err:
            self.logger.error("Missing required metadata key: {0}".format(err))
            raise
        attributes = {}
        for sample_id in self.sample_ids:
            maf_path = os.path.join(self.input_directory, self.input_files[sample_id])
            mx_metrics = mutation_extended_metrics(maf_path, bed_path, tcga_path, cancer_type)
            sample_attributes = {
                constants.TMB_PER_MB_KEY: mx_metrics.get_tmb()
            }
            attributes[sample_id] = sample_attributes
        return attributes
    
    def get_gene_names(self):
        """Find gene names from the input MAF files"""
        if self.gene_names:
            return self.gene_names
        gene_name_set = set()
        for sample_id in self.sample_ids:
            # pandas read_csv() will automatically decompress .gz input
            self.logger.debug("Reading gene names from %s/%s" % (self.input_directory, input_file))
            df = pd.read_csv(
                self.get_input_path(sample_id),
                delimiter="\t",
                usecols=[self.HUGO_SYMBOL],
                comment="#"
            )
            sample_gene_names = set(df[self.HUGO_SYMBOL].tolist())
            if len(gene_name_set) == 0:
                gene_name_set = sample_gene_names
            elif sample_gene_names != gene_name_set:
                self.logger.warning("Gene name sets are not consistent between input MAF files")
        # convert to list and sort
        gene_names = sorted(list(gene_name_set))
        self.gene_names = gene_names # store the gene names in case needed later
        return gene_names

    def get_metrics_by_gene(self, sample_id):
        """Find gene-level mutation metrics. Chromosome name only for now; can add others."""
        df = pd.read_csv(
            self.get_input_path(sample_id),
            delimiter="\t",
            usecols=[self.HUGO_SYMBOL, self.CHROMOSOME],
            comment="#"
        )
        metrics_by_gene = {}
        for index, row in df.iterrows():
            metrics_by_gene[row[self.HUGO_SYMBOL]] = {self.CHROMOSOME: row[self.CHROMOSOME]}
        return metrics_by_gene

    def write_data(self, out_dir):
        """cBioPortal. Write mutation data table.

        - Read mutation data in MAF format and output in cBioPortal's required MAF format
        - May enable VCF input at a later date
        - see https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#mutation-data
        - required modules: vcf2maf/1.6.17, vep/92.0, vep-hg19-cache/92, hg19/p13
        """
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

    def write(self, out_dir):
        self.write_data(out_dir)
        self.write_meta(out_dir)

class segmented(genetic_alteration):
    """
    Segmented data format from cBioPortal; input is SEG files.

    Currently supports Elba output only, not cBioPortal.
    """

    MINIMUM_ABS_SEG_MEAN = 0.2

    def _find_all_sample_attributes(self):
        """Find FGA for each SEG file"""
        attributes = {}
        for sample_id in self.sample_ids:
            seg_path = os.path.join(self.input_directory, self.input_files[sample_id])
            sample_attributes = {
                constants.FRACTION_GENOME_ALTERED_KEY: self._find_fga(seg_path, sample_id)
            }
            attributes[sample_id] = sample_attributes
        return attributes

    def _find_fga(self, seg_path, sample_id):
        seg = pd.read_csv(seg_path, sep='\t', skiprows= 0)
        # ID column of .seg file may be of the form ${SAMPLE_ID}.tumour.bam.varscanSomatic
        # So, select rows where the ID column starts with $SAMPLE_ID
        seg_sample = seg.loc[seg.ID.str.contains("^"+sample_id)]
        seg_alt = seg_sample.loc[abs(seg_sample["seg.mean"]) > self.MINIMUM_ABS_SEG_MEAN]
        denom = sum(seg_sample['loc.end'] - seg_sample['loc.start'])
        try:
            fga = sum(seg_alt['loc.end'] - seg_alt['loc.start'])/denom
        except ZeroDivisionError:
            self.logger.warning('FGA interval has zero width; FRACTION_GENOME_ALTERED is NA')
            fga = "NA"
        return fga

    def get_metrics_by_gene(self, sample_id):
        """Return an empty dictionary, because SEG data has no gene-level metrics"""
        self.logger.debug("SEG data has no gene-level metrics, only sample-level; returning empty dictionary")
        return {}
