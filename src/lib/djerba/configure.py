"""Configure an INI file with Djerba inputs"""

import logging
import os
from math import log2
import urllib.request as request
from urllib.error import URLError, HTTPError
import json

from djerba.sequenza import sequenza_reader, SequenzaError
import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.util.logger import logger
from djerba.util.provenance_reader import provenance_reader, sample_name_container
from djerba.util.validator import path_validator

try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class configurer(logger):
    """
    Class to do configuration in main Djerba method
    Discover and apply param updates
    Param updates are automatically extracted from data sources, eg. file provenance
    """

    # data filenames
    ENSCON_NAME = 'ensemble_conversion_hg38.txt'
    ENTCON_NAME = 'entrez_conversion.txt'
    GENEBED_NAME = 'gencode_v33_hg38_genes.bed'
    ONCOLIST_NAME = '20200818-oncoKBcancerGeneList.tsv'
    ONCOTREE_NAME = '20201201-OncoTree.txt'
    MUTATION_NONSYN_NAME = 'mutation_types.nonsynonymous'
    GENELIST_NAME = 'targeted_genelist.txt'
    TMBCOMP_NAME = 'tmbcomp.txt'

    # TODO validate that discovered config paths are readable

    def __init__(self, config, wgs_only, failed, log_level=logging.WARNING, log_path=None):
        self.config = config
        self.wgs_only = wgs_only
        self.failed = failed
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        if self.wgs_only:
            self.logger.info("Configuring Djerba for WGS-only report")
        else:
            self.logger.info("Configuring Djerba for WGS+WTS report")
        provenance = self.config[ini.SETTINGS][ini.PROVENANCE]
        project = self.config[ini.INPUTS][ini.PROJECT_ID]
        donor = self.config[ini.INPUTS][ini.PATIENT]
        self.reader = provenance_reader(provenance, project, donor, self._get_samples(),
                                        log_level=log_level, log_path=log_path)

    def _get_samples(self):
        """
        Get sample name inputs for provenance reader
        Either None, or a dictionary with WG T/N and (optionally) WT sample names
        "Sample name" here is the sample_name column in file provenance (column 14, 1-indexed)
        """
        samples = sample_name_container()
        if self.config.has_option(ini.DISCOVERED, ini.SAMPLE_NAME_WG_N):
            samples.set_wg_n(self.config[ini.DISCOVERED][ini.SAMPLE_NAME_WG_N])
        if self.config.has_option(ini.DISCOVERED, ini.SAMPLE_NAME_WG_T):
            samples.set_wg_t(self.config[ini.DISCOVERED][ini.SAMPLE_NAME_WG_T])
        if self.config.has_option(ini.DISCOVERED, ini.SAMPLE_NAME_WT_T):
            samples.set_wt_t(self.config[ini.DISCOVERED][ini.SAMPLE_NAME_WT_T])
        if not samples.is_valid():
            msg = "Sample names in INI are not valid; requires WG/N, WG/T, and optionally WT/T; "+\
                  " found {0}".format(samples)
            self.logger.error(msg)
            raise RuntimeError(msg)
        else:
            self.logger.debug("Found sample names from INI input: {0}".format(samples))
        return samples

    def _compare_coverage_to_target(self):
        coverage = self.config.getfloat(ini.DISCOVERED, ini.MEAN_COVERAGE)
        target = self.config.getfloat(ini.DISCOVERED, ini.TARGET_COVERAGE)
        if coverage >= target:
            msg = "Mean coverage {0}X is sufficient for target depth of {1}X.".format(coverage, target)
            self.logger.info(msg)
        else:
            # if coverage is insufficient, issue a warning
            # do not force the report to fail; we want the option to proceed if desired
            msg = "Mean coverage {0}X is NOT sufficient for target depth of {1}X. ".format(coverage, target)+\
                  "Check coverage and target in config INI are correct. A failed report may be required."
            self.logger.warning(msg)

    def find_data_files(self):
        data_files = {}
        if self.config.has_option(ini.DISCOVERED, ini.DATA_DIR):
            data_dir = self.config[ini.DISCOVERED][ini.DATA_DIR]
        else:
            data_dir = os.path.join(os.path.dirname(__file__), constants.DATA_DIR_NAME)
        data_dir = os.path.realpath(data_dir)
        data_files[ini.DATA_DIR] = data_dir
        # use values from the input config, if available; otherwise, fall back to DATA_DIR
        s = self.config[ini.SETTINGS]
        data_files[ini.ENSCON] = s.get(ini.ENSCON) if s.get(ini.ENSCON) else os.path.join(data_dir, self.ENSCON_NAME)
        data_files[ini.ENTCON] = s.get(ini.ENTCON) if s.get(ini.ENTCON) else os.path.join(data_dir, self.ENTCON_NAME)
        data_files[ini.GENE_BED] = s.get(ini.GENE_BED) if s.get(ini.GENE_BED) else os.path.join(data_dir, self.GENEBED_NAME)
        data_files[ini.GENOMIC_SUMMARY] = s.get(ini.GENOMIC_SUMMARY) if s.get(ini.GENOMIC_SUMMARY) else os.path.join(data_dir, constants.GENOMIC_SUMMARY_FILENAME)
        data_files[ini.ONCO_LIST] = s.get(ini.ONCO_LIST) if s.get(ini.ONCO_LIST) else os.path.join(data_dir, self.ONCOLIST_NAME)
        data_files[ini.ONCOTREE_DATA] = s.get(ini.ONCOTREE_DATA) if s.get(ini.ONCOTREE_DATA) else os.path.join(data_dir, self.ONCOTREE_NAME)
        data_files[ini.MUTATION_NONSYN] = s.get(ini.MUTATION_NONSYN) if s.get(ini.MUTATION_NONSYN) else os.path.join(data_dir, self.MUTATION_NONSYN_NAME)
        data_files[ini.GENE_LIST] = s.get(ini.GENE_LIST) if s.get(ini.GENE_LIST) else os.path.join(data_dir, self.GENELIST_NAME)
        data_files[ini.TMBCOMP] = s.get(ini.TMBCOMP) if s.get(ini.TMBCOMP) else os.path.join(data_dir, self.TMBCOMP_NAME)
        data_files[ini.TECHNICAL_NOTES] = s.get(ini.TECHNICAL_NOTES) if s.get(ini.TECHNICAL_NOTES) else os.path.join(data_dir, constants.TECHNICAL_NOTES_FILENAME)
        return data_files

    def discover_primary(self):
        updates = {}
        updates.update(self.reader.get_identifiers())
        if self.failed:
            self.logger.info("Failed report mode, omitting workflow output discovery")
        else:
            self.logger.info("Searching provenance for workflow output files")
            updates[ini.SEQUENZA_FILE] = self.reader.parse_sequenza_path()
            updates[ini.MAF_FILE] = self.reader.parse_maf_path()
            updates[ini.MSI_FILE] = self.reader.parse_msi_path()
            if not self.wgs_only:
                updates[ini.MAVIS_FILE] = self.reader.parse_mavis_path()
                updates[ini.GEP_FILE] = self.reader.parse_gep_path()
        updates.update(self.reader.get_sample_names())
        updates.update(self.find_data_files())
        if self.config.has_option(ini.DISCOVERED, ini.CBIO_STUDY_ID):
            msg = "Using manually configured cBioportal project name {0}".format(self.config[ini.DISCOVERED][ini.CBIO_STUDY_ID])
            self.logger.info(msg)
        else:
            project_id = self.config[ini.INPUTS][ini.PROJECT_ID]
            try:
                cbio_study_id = pull_qc(self.config).fetch_cbio_name(project_id)
                msg = "Found cbioportal-study-id {0} for project {1} in Shesmu".format(updates[ini.CBIO_STUDY_ID], project_id)
                self.logger.info(msg)
            except KeyError:
                cbio_study_id = project_id
                msg = "Couldn't find the project in Shesmu. cbioportal-study-id will default to project-id {0}".format(project_id)
                self.logger.info(msg)
            updates[ini.CBIO_STUDY_ID] = cbio_study_id
        return updates

    def discover_secondary(self):
        updates = {}
        # configure Sequenza: gamma, solution, purity, ploidy.
        # Requires Sequenza file from discover_primary()
        reader = sequenza_reader(self.config[ini.DISCOVERED][ini.SEQUENZA_FILE])
        gamma = self.config.getint(ini.DISCOVERED, ini.SEQUENZA_GAMMA, fallback=None)
        solution = self.config.get(ini.DISCOVERED, ini.SEQUENZA_SOLUTION, fallback=None)
        # get_default_gamma_id() returns (gamma, solution)
        if gamma == None:
            gamma = reader.get_default_gamma_id()[0]
            self.logger.info("Automatically generated Sequenza gamma: {0}".format(gamma))
        else:
            self.logger.info("User-supplied Sequenza gamma: {0}".format(gamma))
        if solution == None:
            solution = constants.SEQUENZA_PRIMARY_SOLUTION
            self.logger.info("Alternate Sequenza solution not supplied, defaulting to primary")
        try:
            purity = reader.get_purity(gamma, solution)
            ploidy = reader.get_ploidy(gamma, solution)
        except SequenzaError as err:
            msg = "Unable to find Sequenza purity/ploidy: {0}".format(err)
            self.logger.error(msg)
            raise
        self.logger.info("Sequenza purity {0}, ploidy {1}".format(purity, ploidy))
        updates[ini.SEQUENZA_GAMMA] = gamma
        updates[ini.SEQUENZA_SOLUTION] = solution
        updates[ini.PLOIDY] = ploidy
        updates[ini.PURITY] = purity
        # Configure with QC-ETL and Pinery: mean coverage, target coverage, callability.
        # Requires tumour and requisition IDs from discover_primary()
        tumour_id = self.config[ini.DISCOVERED][ini.TUMOUR_ID]
        qc_retriever = pull_qc(self.config)
        if self.config.has_option(ini.DISCOVERED, ini.MEAN_COVERAGE):
            msg = "Using manually configured mean coverage: {0}".format(self.config[ini.DISCOVERED][ini.MEAN_COVERAGE])
            self.logger.info(msg)
        else:
            try:
                coverage = qc_retriever.fetch_coverage_etl_data(tumour_id)
            except MissingQCETLError as e:
                msg = "Coverage not supplied by user, and cannot be retrieved from QC-ETL for tumour_id {0}: {1}".format(tumour_id, e)
                self.logger.error(msg)
                raise
            self.logger.info("Using mean coverage from QC-ETL: {0}".format(coverage))
            updates[ini.MEAN_COVERAGE] = coverage
        if self.config.has_option(ini.DISCOVERED, ini.PCT_V7_ABOVE_80X):
            msg = "Using manually configured callability: {0}".format(self.config[ini.DISCOVERED][ini.PCT_V7_ABOVE_80X])
            self.logger.info(msg)
        else:
            try:
                callability = qc_retriever.fetch_callability_etl_data(tumour_id)
            except MissingQCETLError as e:
                msg = "Callability not supplied by user, and cannot be retrieved from QC-ETL for tumour_id {0}: {1}".format(tumour_id, e)
                self.logger.error(msg)
                raise
            self.logger.info("Using callability from QC-ETL: {0}".format(coverage))
            updates[ini.PCT_V7_ABOVE_80X] = callability
        if self.config.has_option(ini.DISCOVERED, ini.TARGET_COVERAGE):
            msg = "Using manually configured target coverage: {0}".format(self.config[ini.DISCOVERED][ini.TARGET_COVERAGE])
            self.logger.info(msg)
        else:
            req_id = self.config[ini.INPUTS][ini.REQ_ID]
            try:
                target_coverage = qc_retriever.fetch_pinery_assay(req_id)
            except (MissingPineryError, UnsupportedAssayError) as e:
                msg = "Target coverage not supplied by user, and cannot be retrieved from Pinery for requisition ID {0}: {1}".format(req_id, e)
                self.logger.error(msg)
                raise
            self.logger.info("Using target coverage from Pinery: {0}".format(target_coverage))
            updates[ini.TARGET_COVERAGE] = target_coverage
        return updates

    def run(self, out_path):
        """Main method to run configuration"""
        self.logger.info("Djerba config started")
        # first pass -- update basic parameters
        self.update_primary()
        if self.failed:
            self.logger.info("Failed report mode; omitting secondary/tertiary config updates")
            required = [ini.PURITY, ini.PLOIDY]
            if not all([self.config.has_option(ini.DISCOVERED, x) for x in required]):
                msg = "The following parameters must be entered manually for failed reports: {0}".format(required)
                self.logger.error(msg)
                raise RuntimeError(msg)
        else:
            self.logger.info("Applying sequenza/logR config updates")
            # second pass -- update Sequenza params using base values
            self.update_secondary()
            # third pass -- logR cutoffs using the updated purity
            self.update_tertiary()
            self._compare_coverage_to_target()
        with open(out_path, 'w') as out_file:
            self.config.write(out_file)
        self.logger.info("Djerba config finished; wrote output to {0}".format(out_path))

    def update(self, updates):
        """
        Apply discovered updates to the configuration; do not overwrite user-supplied parameters
        If discovered update is None, and user-supplied parameter is missing, raise an error
        """
        if not self.config.has_section(ini.DISCOVERED):
            self.config.add_section(ini.DISCOVERED)
        for key in updates.keys():
            # *do not* overwrite existing params
            # allows user to specify params which will not be overwritten by automated discovery
            if not self.config.has_option(ini.DISCOVERED, key):
                if updates[key] == None:
                    self.logger.debug('Error applying updates: {0}'.format(updates))
                    msg = "Failed to update parameter '{0}' in section [{1}]. ".format(key, ini.DISCOVERED)+\
                        "Djerba was unable to discover the parameter automatically, and "+\
                        "no user-supplied value was found. Run Djerba with --debug for more "+\
                        "details. Manually specifying the parameter in the user-supplied INI file "+\
                        "may allow Djerba to run successfully."
                    self.logger.error(msg)
                    raise MissingConfigError(msg)
                else:
                    self.config[ini.DISCOVERED][key] = str(updates[key])

    def update_primary(self):
        """
        Discover and apply first-pass updates to the configuration; do not overwrite user-supplied parameters
        """
        self.update(self.discover_primary())

    def update_secondary(self):
        """
        Discover and apply second-pass updates to the configuration; do not overwrite user-supplied parameters
        Secondary parameters include Sequenza purity/ploidy
        May depend on discovered value of the Sequenza output file, so we do these after completing first pass
        """
        self.update(self.discover_secondary())

    def update_tertiary(self):
        """
        Discover and apply third-pass updates to the configuration; do not overwrite user-supplied parameters
        Tertiary parameters are logR cutoffs
        May depend on the discovered value of Sequenza purity, so we do these after completing second pass
        """
        purity = self.config.getfloat(ini.DISCOVERED, ini.PURITY)
        self.update(log_r_cutoff_finder().cutoffs(purity))

class log_r_cutoff_finder:
    """Find logR cutoff values; based on legacy Perl script logRcuts.pl"""

    MIN_LOG_ARG = 0.0078125 # 1/128 = 2^(-7)

    def cutoffs(self, purity):
        one_copy = purity / 2.0 # essentially assuming ploidy 2 (more accurately, defining htzd as loss of 0.5 ploidy and hmzd as loss of 1 ploidy)
        # expected values for different states
        htzd = self.log2_with_minimum(1 - one_copy)
        hmzd = self.log2_with_minimum(1 - (2*one_copy))
        gain = self.log2_with_minimum(1 + one_copy)
        ampl = self.log2_with_minimum(1 + (2*one_copy))
        # cutoffs halfway between 0 and 1 copy, and halfway between 1 and 2 copies
        cutoffs = {
            ini.LOG_R_HTZD: htzd/2.0,
            ini.LOG_R_HMZD: (hmzd-htzd)/2.0 + htzd,
            ini.LOG_R_GAIN: gain/2.0,
            ini.LOG_R_AMPL: (ampl-gain)/2.0 + gain
        }
        return cutoffs

    def log2_with_minimum(self, x):
        """Return log2(x), or log2(min) if x < min; hack to avoid log(0)"""
        if x < self.MIN_LOG_ARG:
            return log2(self.MIN_LOG_ARG)
        else:
            return log2(x)

class pull_qc(logger):

    class Requisition():
        def __init__(self, pinery_requisition, pinery_assay):
            self.id: int = pinery_requisition['id']
            self.name: str = pinery_requisition['name']
            self.assay: str = pinery_assay['name']
            self.assay_id: int = pinery_assay['id']
            self.assay_description: str = pinery_assay['description']
            self.assay_version: str = pinery_assay['version']

    def __init__(self, config, log_level=logging.WARNING, log_path=None):
        self.config = config
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.pinery_url = self.config[ini.SETTINGS][ini.PINERY_URL]
        self.qcetl_cache = self.config[ini.SETTINGS][ini.QCETL_CACHE]
        self.cbio_path = self.config[ini.SETTINGS][ini.CBIO_PROJECT_PATH]
        path_validator(log_level, log_path).validate_input_file(self.cbio_path)
        self.etl_cache = QCETLCache(self.qcetl_cache)

    def fetch_callability_etl_data(self,tumour_id):
        cached_callabilities = self.etl_cache.mutectcallability.mutectcallability
        columns_of_interest = gsiqcetl.column.MutetctCallabilityColumn
        data = cached_callabilities.loc[
            (cached_callabilities[columns_of_interest.GroupID] == tumour_id),
            [columns_of_interest.GroupID, columns_of_interest.Callability]
            ]
        if len(data) > 0:
            callability = round(data.iloc[0][columns_of_interest.Callability].item() * 100,1)
            return callability
        else:
            msg = "Djerba couldn't find the callability associated with tumour_id {0} in QC-ETL. ".format(tumour_id)
            self.logger.debug(msg)
            raise MissingQCETLError(msg)
        
    def fetch_cbio_name(self,project_id):
        with open(self.cbio_path) as in_file:
            data = json.loads(in_file.read())
        cbioportal_project_id = data['values'][project_id]['cbioportal_project']
        return cbioportal_project_id
        
    def fetch_coverage_etl_data(self,tumour_id):
        cached_coverages = self.etl_cache.bamqc4merged.bamqc4merged
        columns_of_interest = gsiqcetl.column.BamQc4MergedColumn
        data = cached_coverages.loc[
            (cached_coverages[columns_of_interest.GroupID] == tumour_id),
            [columns_of_interest.GroupID, columns_of_interest.CoverageDeduplicated]
            ]
        if len(data) > 0:
            coverage_value = round(data.iloc[0][columns_of_interest.CoverageDeduplicated].item(),1)
            return(coverage_value)
        else:
            msg = "Djerba couldn't find the coverage associated with tumour_id {0} in QC-ETL. ".format(tumour_id)
            self.logger.debug(msg)
            raise MissingQCETLError(msg)

    def fetch_pinery_assay(self,requisition_name: str):
        try:
            pinery_requisition = self.pinery_get(f'/requisition?name={requisition_name}')
        except HTTPError:
            msg = "Djerba couldn't find the assay associated with requisition {0} in Pinery. ".format(requisition_name)
            self.logger.debug(msg)
            raise MissingPineryError(msg)
        if len(pinery_requisition) > 0:
            try:
                pinery_assay = self.pinery_get(f'/assay/{pinery_requisition["assay_id"]}')
            except KeyError:
                msg = "Djerba couldn't find an assay type associated with requisition {0} in Pinery. ".format(requisition_name)
                self.logger.debug(msg)
                raise UnsupportedAssayError(msg)
            requisition = self.Requisition(pinery_requisition, pinery_assay)
            if (requisition.assay == "WGTS - 80XT/30XN") | (requisition.assay == "WGS - 80XT/30XN") :
                requisition_target = 80
            elif (requisition.assay == "WGTS - 40XT/30XN") | (requisition.assay == "WGS - 40XT/30XN"):
                requisition_target = 40
            else:
                msg = "The assay {0} associated with requisition {1} in Pinery is not clinically supported. ".format(requisition.assay,requisition_name)
                self.logger.debug(msg)
                raise UnsupportedAssayError(msg)
            return(requisition_target)
        else:
            msg = "Djerba couldn't find the assay associated with requisition {0} in Pinery. ".format(requisition_name)
            self.logger.debug(msg)
            raise MissingPineryError(msg)

    def pinery_get(self,relative_url: str) -> dict:
        if not relative_url.startswith('/'):
            raise RuntimeError('Invalid relative url')
        return json.load(request.urlopen(f'{self.pinery_url}{relative_url}'))

class MissingConfigError(Exception):
    pass

class MissingQCETLError(Exception):
    pass 

class MissingPineryError(Exception):
    pass

class UnsupportedAssayError(Exception):
    pass
