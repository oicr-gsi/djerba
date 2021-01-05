"""Classes to handle Djerba configuration data"""

import configparser
import json
import jsonschema
import logging
import os
import pandas as pd
import subprocess
from glob import glob
from jsonschema.exceptions import ValidationError, SchemaError
from djerba.utilities.base import base
from djerba.utilities import constants


class builder(base):
    """Build a Djerba config data structure for Elba output"""

    ### output keys
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

    ### directory names for constructing input paths
    SEQUENZA = 'sequenza'
    REVIEW = 'review'
    VEP = 'variantEffectPredictor'
    RSEM = 'RSEM'
    
    ### input keys -- old style, for "build"
    CUSTOM_DIR_INPUT = 'custom_dir'
    GENE_TSV_INPUT = GENE_TSV_KEY
    SAMPLE_TSV_INPUT = SAMPLE_TSV_KEY
    MAF_INPUT = 'maf'
    BED_INPUT = BED_PATH_KEY
    CANCER_TYPE_INPUT = CANCER_TYPE_KEY
    ONCOKB_INPUT = ONCOKB_TOKEN_KEY
    TCGA_INPUT = TCGA_PATH_KEY
    VCF_INPUT = FILTER_VCF_KEY
    SEG_INPUT = 'seg'
    ### input keys -- new style, for "build_from_cgi_inputs"
    STUDY_ID_INPUT = 'study_id'
    PATIENT_ID_INPUT = 'patient_id'
    ANALYSIS_UNIT_INPUT = 'analysis_unit'
    ONCOTREE_CODE_INPUT = 'oncotree_code'
    VERSION_NUM_INPUT = 'version_num'
    DATA_DIR_INPUT = 'data_dir'
    ONCOTREE_PATH_INPUT = 'oncotree_data'

    ### selections.ini keys
    INI_PURITY = 'purity'
    INI_PLOIDY = 'ploidy'
    INI_GAMMA = 'gamma'
    INI_DATE = 'date'
    INI_REV_1 = 'reviewer1'
    INI_REV_2 = 'reviewer2'
    INI_KEYS = [INI_PURITY, INI_PLOIDY, INI_GAMMA, INI_DATE, INI_REV_1, INI_REV_2]
    
    ### Defaults for CGI config building
    DEFAULT_DATA_DIR = '/.mounts/labs/TGL/cap'
    DEFAULT_ONCOTREE_FILENAME = '20201201-OncoTree.txt' # from CGI-Tools repo

    def __init__(self, sample_id, log_level=logging.WARN, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.log_path = log_path
        self.sample_id = sample_id

    def _check_cgi_inputs(self, args):
        """Check required arguments are present for build_from_cgi_inputs"""
        # existence of paths etc. will be checked upstream, eg. in the calling script
        required_args = [
            self.STUDY_ID_INPUT,
            self.PATIENT_ID_INPUT,
            self.ANALYSIS_UNIT_INPUT,
            self.ONCOTREE_CODE_INPUT,
            self.VERSION_NUM_INPUT,
            self.DATA_DIR_INPUT, # required but may be None
            self.ONCOTREE_PATH_INPUT # required but may be None
        ]
        if not set(required_args).equals(set(args.keys())):
            expected = str(sorted(required_args))
            found = str(sorted(list(args.keys())))
            msg = "Incorrect arguments; expected %s, found %s" % (expected, found)
            self.logger.error(msg)
            raise DjerbaConfigError(msg)

    def _find_fus_path(self, version_dir):
        """Find the Mavis summary path"""
        fus_pattern = os.path.join(
            version_dir, 'mavis', 'execution', 'summary', 'mavis_summary_all_WG.*.tab'
        )
        fus_paths = glob(fus_pattern)
        error_msg = None
        if len(fus_paths)==0:
            error_msg = "No fusfile in %s; failure to run Mavis?" % version_dir
        elif len(fus_paths)>1:
            error_msg = "Multiple fusfiles in %s; " % version_dir +\
                        "should be only one mavis_summary_all_WG.*.tab"
        if error_msg:
            self.logger.error(error_msg)
            raise DjerbaConfigError(error_msg)
        fus_path = fus_paths.pop()
        return fus_path

    def _read_cgi_inputs(self, args):
        """Find and process CGI data for generating Djerba config"""
        self._check_cgi_inputs(args)
        analysis_unit = args[self.ANALYSIS_UNIT_INPUT]
        version = args[self.VERSION_NUM_INPUT]
        if args[self.DATA_DIR_INPUT]:
            data_dir = args[self.DATA_DIR_INPUT]
        else:
            data_dir = self.DEFAULT_DATA_DIR
        # find input files
        patient_dir = os.path.join(data_dir, args[self.STUDY_ID_INPUT], args[self.PATIENT_ID_INPUT])
        version_dir = os.path.join(patient_dir, analysis_unit, version)
        ms_path = os.path.join(patient_dir, "mastersheet-v{0}.psv".format(version))
        ini_path = os.path.join(version_dir, self.SEQUENZA, self.REVIEW, 'selection.ini')
        for input_path in (ms_path, ini_path):
            if not os.access(input_path, os.R_OK):
                msg = "Cannot read input path %s" % input_path
                self.logger.error(msg)
                raise DjerbaConfigError(msg)
        # process the input files
        [tumor_id, normal_id] = self._read_mastersheet(ms_path, args[self.ANALYSIS_UNIT_INPUT])
        selections = self._read_selections(ini_path)
        [cancer_type, cancer_desc] = self._read_oncotree(
            args[self.ONCOTREE_CODE_INPUT]
            args[self.ONCOTREE_PATH_INPUT]
        )
        # construct additional file paths
        fus_path = self._find_fus_path(version_dir)
        maf_path = os.path.join(
            version_dir, self.VEP, '{0}.maf.gz'.format(analysis_unit)
        )
        seg_path = os.path.join(
            version_dir, self.SEQUENZA, self.REVIEW, "{0}.seg".format(selections[self.INI_GAMMA])
        )
        gep_path = os.path.join(
            version_dir, self.RSEM, "{0}.genes.results".format(analysis_unit)
        )
        # check path readability
        unreadable = []
        for file_path in [fus_path, maf_path, seg_path, gep_path]:
            if not os.access(file_path, os.R_OK):
                unreadable.append(file_path)
        if len(unreadable)>0:
            msg = "Cannot read data files: {0}".format(str(sorted(unreadable)))
            self.logger.error(msg)
            raise DjerbaConfigError(msg)
        scalars = [tumor_id, normal_id, cancer_type, cancer_desc]
        paths = [fus_path, maf_path, seg_path, gep_path]
        return cgi_params(scalars, paths, selections)
    
    def _read_mastersheet(self, ms_path, analysis_unit):
        """Parse the mastersheet file to find tumor/normal IDs"""
        # TODO reimplement the bash one-liner in Python
        template = """awk -F "|" -v OFS="|" -v u={0} '{ if (($11 == u) && ($6 =="WG")) {print $11,$12,$15} }' {1} | awk -F "|" '!seen[$1]++' | cut -f{2} -d'|'"""
        output = []
        for col in [2,3]: # column 2 = tumor, column 3 = normal
            args = template.format(analysis_unit, ms_path, col)
            try:
                result = subprocess.run(args, capture_output=True, check=True)
            except CalledProcessError as cpe:
                msg = "Non-zero exit code from bash one-liner "+\
                      "to find tumor/normal ID: {0}".format(args)
                self.logger.error(msg)
                raise DjerbaConfigError(msg) from cpe
            output.append(result.stdout.decode(constants.TEXT_ENCODING))
        return output

    def _read_oncotree(self, oncocode, oncotree_path):
        """Read the cancer type and cancer type description"""
        if self.is_null(oncotree_path):
            oncotree_path = os.path.join(
                os.path.dirname(__file__),
                constants.DATA_DIRNAME,
                self.DEFAULT_ONCOTREE_FILENAME 
            )
        # TODO reimplement the bash one-liners in Python
        args_1 = """grep -iw {0} {1} | cut -f1 | sed -e 's/([^()]*)//g' | sort | uniq | sed 's/[[:space:]]*$//'""".format(oncocode, oncotree_path) # CANCER_TYPE
        args_2 = """cat {0} | tr '\t' '\n' | grep -iw {1} | sed "s/({2})//" | sed 's/[[:space:]]*$//'""".format(oncotree_path, oncocode, oncocode) # CANCER_TYPE_DESCRIPTION
        output = []
        for args in [args_1, args_2]:
            try:
                result = subprocess.run(args, capture_output=True, check=True)
            except CalledProcessError as cpe:
                msg = "Non-zero exit code from bash one-liner "+\
                      "to cancer type/description from oncotree: {0}".format(args)
                self.logger.error(msg)
                raise DjerbaConfigError(msg) from cpe
            output.append(result.stdout.decode(constants.TEXT_ENCODING))
        return output

    def _read_selections(self, ini_path):
        """
        Read the selections INI file; check required options are present.
        Returns a dictionary-like configparser object.
        """
        # need to prepend a dummy section header to use the configparser module
        # see https://stackoverflow.com/questions/2885190/using-configparser-to-read-a-file-without-section-name
        cp = configparser.ConfigParser()
        section = constants.SECTION_DEFAULT
        with open(ini_path) as stream:
            cp.read_string("[{0}]\n".format(section) + stream.read())
        missing = []
        for key in self.INI_KEYS:
            if not cp.has_option(section, key):
                missing.append(key)
            elif self.is_null(cp.get(section, key)):
                missing.append(key)
        if len(missing)>0:
            msg = "Required values in selections INI are null or "+\
                  "missing: {0}".format(str(sorted(missing)))
            self.logger.error(msg)
            raise DjerbaConfigError(msg)
        return cp[section]
    
    def build(self, args):
        """
        Build a config data structure from the given arguments
        TODO Add clinical_report_meta
        TODO This method may become obsolete given build_from_cgi
        """
        config = {}
        samples = [
            {constants.SAMPLE_ID_KEY: self.sample_id}
        ]
        config[constants.SAMPLES_KEY] = samples
        genetic_alterations = []
        custom_config = self.build_custom(
            args[self.CUSTOM_DIR_INPUT],
            args[self.GENE_TSV_INPUT],
            args[self.SAMPLE_TSV_INPUT]
        )
        genetic_alterations.append(custom_config)
        mutex_config = self.build_mutex(
            args[self.MAF_INPUT],
            args[self.BED_INPUT],
            args[self.CANCER_TYPE_INPUT],
            args[self.ONCOKB_INPUT],
            args[self.TCGA_INPUT],
            args[self.VCF_INPUT]
        )
        genetic_alterations.append(mutex_config)
        seg_config = self.build_segmented(args[self.SEG_INPUT])
        genetic_alterations.append(seg_config)
        config[constants.GENETIC_ALTERATIONS_KEY] = genetic_alterations
        self.logger.info("Djerba configuration complete; validating against schema")
        validator(self.logger.getEffectiveLevel(), self.log_path).validate(config, self.sample_id)
        return config

    def build_from_cgi_inputs(self, args):
        """Build Djerba config from CGI data sources, eg. the mastersheet"""
        # TODO construct the config in line with CGI-Tools 3-configureSingleSample.sh
        # TODO create a class for the mastersheet, with input validation
        # TODO may later want to generate mastersheet within Djerba, instead of by shell script
        # "mastersheet" extracted from file provenance by 1-linkNiassa.sh
        cgi_params = self._read_cgi_inputs(args)
        config = {}
        # populate sample attributes from the CGI data
        sample = {
            constants.SAMPLE_ID_KEY: self.sample_id,
            constants.CANCER_TYPE_KEY: cgi_params.cancer_type,
            constants.CANCER_TYPE_DETAILED_KEY: args[self.ONCOTREE_CODE_INPUT],
            constants.CANCER_TYPE_DESCRIPTION_KEY: cgi_params.cancer_desc,
            constants.SEQUENZA_PLOIDY_KEY: cgi_params.selections.get(self.INI_PURITY),
            constants.SEQUENZA_PURITY_FRACTION_KEY: cgi_params.selections.get(self.INI_PLOIDY)
        }
        config[constants.SAMPLES_KEY] = [sample]
        clinical_report_meta = self.build_clinical_report_meta(args, cgi_params)
        config[constants.CLINICAL_REPORT_META_KEY] = clinical_report_meta
        # from here on, same as older build() method
        genetic_alterations = []
        custom_config = self.build_custom(
            args[self.CUSTOM_DIR_INPUT],
            args[self.GENE_TSV_INPUT],
            args[self.SAMPLE_TSV_INPUT]
        )
        genetic_alterations.append(custom_config)
        mutex_config = self.build_mutex(
            clinical_report_meta.get(constants.MAF_FILE_KEY),
            args[self.BED_INPUT],
            args[self.CANCER_TYPE_INPUT],
            args[self.ONCOKB_INPUT],
            args[self.TCGA_INPUT],
            args[self.VCF_INPUT]
        )
        genetic_alterations.append(mutex_config)
        seg_config = self.build_segmented(clinical_report_meta.get(constants.SEG_FILE_KEY))
        genetic_alterations.append(seg_config)
        config[constants.GENETIC_ALTERATIONS_KEY] = genetic_alterations
        self.logger.info("Djerba configuration complete; validating against schema")
        validator(self.logger.getEffectiveLevel(), self.log_path).validate(config, self.sample_id)
        return config

    def build_clinical_report_meta(self, args, cgi_params):
        """Build the clinical_report_meta config object"""
        """
        Schema:
        meta =  {
	    "report_version": {"type": ["number", "string"]},
	    "study_id": {"type": "string"},
	    "patient": {"type": "string"},
	    "analysis_unit": {"type": "string"},
	    "tumor_id": {"type": "string"},
	    "normal_id": {"type": "string"},
	    "gamma": {"type": "string"},
	    "maf_file": {"type": "string"},
	    "seg_file": {"type": "string"},
	    "fus_file": {"type": "string"},
	    "gep_file": {"type": "string"}
	}
        """
        meta = {}
        args_keys = [
            self.STUDY_ID_INPUT,
            self.VERSION_NUM_INPUT,
            self.PATIENT_ID_INPUT,
            self.ANALYSIS_UNIT_INPUT
        ]
        for key in args_keys:
            meta[key] = args.get(key)
        meta[constants.TUMOR_ID_KEY] = cgi_params.tumor_id
        meta[constants.NORMAL_ID_KEY] = cgi_params.normal_id
        meta[constants.GAMMA_KEY] = cgi_params.selections.get(self.INI_GAMMA)
        meta[constants.MAF_FILE_KEY] = cgi_params.maf_file
        meta[constants.SEG_FILE_KEY] = cgi_params.seg_file
        meta[constants.FUS_FILE_KEY] = cgi_params.fus_file
        meta[constants.GEP_FILE_KEY] = cgi_params.gep_file
        return meta

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

class cgi_params:
    """Simple container class for results from _read_cgi_inputs"""

    def __init__(self, scalars, paths, selections_config):        
        [self.tumor_id, self.normal_id, self.cancer_type, self.cancer_desc] = scalars
        [self.fus_path, self.maf_path, self.seg_path, self.gep_path] = paths
        # convert the configParser to a dictionary
        self.selections = dict(selections_config.items(constants.SECTION_DEFAULT))

class DjerbaConfigError(Exception):
    pass
