"""Configure an INI file with Djerba inputs"""

import csv
import gzip
import logging
import os
import re

import djerba.util.constants as constants
import djerba.util.provenance_index as index
import djerba.util.ini_fields as ini
from djerba.util.logger import logger

class configurer(logger):
    """
    Class to do configuration in main Djerba method
    Discover and apply param updates to a ConfigParser object
    Param updates are automatically extracted from data sources, eg. file provenance
    """

    # data filenames
    # mutationcode and filterflagexc are obsolete; included in r_script_wrapper.py
    ENSCON_NAME = 'ensemble_conversion_hg38.txt'
    ENTCON_NAME = 'entrez_conversion.txt'
    GENEBED_NAME = 'gencode_v33_hg38_genes.bed'
    ONCOLIST_NAME = '20200818-oncoKBcancerGeneList.tsv'
    ONCOTREE_NAME = '20201201-OncoTree.txt'
    MUTATION_NONSYN_NAME = 'mutation_types.nonsynonymous'
    GENELIST_NAME = 'targeted_genelist.txt'
    TMBCOMP_NAME = 'tmbcomp.txt'

    # TODO validate that discovered config paths are readable

    def __init__(self, config, log_level=logging.WARNING, log_path=None):
        self.config = config
        self.logger = self.get_logger(log_level, __name__, log_path)
        provenance = self.config[ini.SETTINGS][ini.PROVENANCE]
        project = self.config[ini.INPUTS][ini.STUDY_ID]
        donor = self.config[ini.INPUTS][ini.PATIENT]
        self.reader = provenance_reader(provenance, project, donor, log_level, log_path)

    def find_data_files(self):
        data_files = {}
        if self.config[ini.DISCOVERED].get(ini.DATA_DIR):
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
        return data_files

    def discover(self):
        updates = {}
        updates[ini.GEP_FILE] = self.reader.parse_gep_path()
        updates[ini.MAF_FILE] = self.reader.parse_maf_path()
        updates[ini.MAVIS_FILE] = self.reader.parse_mavis_path()
        updates[ini.SEQUENZA_FILE] = self.reader.parse_sequenza_path()
        updates[ini.ANALYSIS_UNIT] = self.reader.find_analysis_unit()
        updates.update(self.reader.find_identifiers())
        updates.update(self.find_data_files())
        return updates

    def run(self, out_path):
        """Main method to run configuration"""
        self.logger.info("Djerba config started")
        self.update()
        with open(out_path, 'w') as out_file:
            self.config.write(out_file)
        self.logger.info("Djerba config finished; wrote output to {0}".format(out_path))

    def update(self):
        """
        Discover and apply updates to the configuration; do not overwrite user-supplied parameters
        If discovered update is None, and user-supplied parameter is missing, raise an error
        """
        updates = self.discover()
        if not self.config.has_section(ini.DISCOVERED):
            self.config.add_section(ini.DISCOVERED)
        for key in updates.keys():
            # *do not* overwrite existing params
            # allows user to specify params which will not be overwritten by automated discovery
            if not self.config.has_option(ini.DISCOVERED, key):
                if updates[key] == None:
                    msg = "Failed to update parameter '{0}' in section [{1}]. ".format(key, ini.DISCOVERED)+\
                        "Djerba was unable to discover the parameter automatically, and "+\
                        "no user-supplied value was found. Run Djerba with --debug for more "+\
                        "details. Manually specifying the parameter in the user-supplied INI file "+\
                        "may allow Djerba to run successfully."
                    self.logger.error(msg)
                    raise MissingConfigError(msg)
                else:
                    self.config[ini.DISCOVERED][key] = updates[key]

class provenance_reader(logger):

    # internal dictionary keys
    ROOT_SAMPLE_NAME_KEY = 'root_sample_name'
    LIMS_ID_KEY = 'lims_id'

    # parent sample attribute keys
    GEO_EXTERNAL_NAME = 'geo_external_name'
    GEO_GROUP_ID = 'geo_group_id'
    GEO_TISSUE_ORIGIN_ID = 'geo_tissue_origin'
    GEO_TISSUE_TYPE_ID = 'geo_tissue_type'
    GEO_TUBE_ID = 'geo_tube_id'

    def __init__(self, provenance_path, project, donor, log_level=logging.WARNING, log_path=None):
        # get provenance for the project and donor
        # if this proves to be too slow, can preprocess the file using zgrep
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Reading provenance for project '%s' and donor '%s' " % (project, donor))
        self.donor = donor
        self.provenance = []
        with gzip.open(provenance_path, 'rt') as infile:
            reader = csv.reader(infile, delimiter="\t")
            for row in reader:
                if row[index.STUDY_TITLE] == project and \
                   row[index.ROOT_SAMPLE_NAME] == donor and \
                   row[index.SEQUENCER_RUN_PLATFORM_ID] != 'Illumina_MiSeq':
                    self.provenance.append(row)
        if len(self.provenance)==0:
            msg = "No provenance records found for project '%s' and donor '%s' " % (project, donor) +\
                "in '%s'" % provenance_path
            self.logger.error(msg)
            raise MissingProvenanceError(msg)
        else:
            self.logger.info("Found %d provenance records" % len(self.provenance))
        # find relevant attributes from provenance
        # start by finding unique combinations of name/attributes/LIMS_ID
        provenance_subset = set()
        for row in self.provenance:
            columns = (
                row[index.ROOT_SAMPLE_NAME],
                row[index.PARENT_SAMPLE_ATTRIBUTES],
                row[index.LIMS_ID]
            )
            provenance_subset.add(columns)
        # parse the 'parent sample attributes' value and get a list of dictionaries
        self.attributes = [self._parse_row_attributes(row) for row in provenance_subset]

    def _filter_rows(self, index, value, rows=None):
        # find matching provenance rows from a list
        if rows == None: rows = self.provenance
        return filter(lambda x: x[index]==value, rows)

    def _filter_metatype(self, metatype, rows=None):
        return self._filter_rows(index.FILE_META_TYPE, metatype, rows)

    def _filter_pattern(self, pattern, rows=None):
        if rows == None: rows = self.provenance
        return filter(lambda x: re.search(pattern, x[index.FILE_PATH]), rows)

    def _filter_workflow(self, workflow, rows=None):
        return self._filter_rows(index.WORKFLOW_NAME, workflow, rows)

    def _get_most_recent_row(self, rows):
        # if input is empty, raise an error
        # otherwise, return the row with the most recent date field (last in lexical sort order)
        # rows may be an iterator; if so, convert to a list
        rows = list(rows)
        if len(rows)==0:
            msg = "Empty input to find most recent row; no rows meet filter criteria?"
            self.logger.debug(msg)
            raise MissingProvenanceError(msg)
        else:
            return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]

    def _get_unique_value(self, key, check, reference=False):
        """
        Get unique value (if any) of key from self.attributes
        Attributes is a list of dictionaries, each corresponding to one or more provenance rows
        If check==True, check the tissue type ID to determine if the row refers to a reference (ie. normal)
        Then:
        - If key is present, confirm that all members of the list have the same value
        - If key does not exist for any member, return None
        - If values for key are inconsistent, return None (additional error checking is done downstream)
        """
        value_set = set()
        for row in self.attributes:
            if check:
                if reference and row.get(self.GEO_TISSUE_TYPE_ID)!='R':
                    continue
                elif not reference and row.get(self.GEO_TISSUE_TYPE_ID)=='R':
                    continue
            value_set.add(row.get(key))
        if len(value_set)==0:
            self.logger.debug("No value found for {0}, reference = {1}".format(key, reference))
            value = None
        elif len(value_set)==1:
            value = list(value_set).pop()
        else:
            msg = "Value for '{0}' with reference={1} is not unique: Found {2}".format(key, reference, value_set)
            self.logger.debug(msg)
            value = None
        return value

    def _id_normal(self, patient_id):
        self.logger.debug("Finding normal ID")
        normal_id = self._id_tumour_normal(patient_id, reference=True)
        self.logger.debug("Found normal ID: {0}".format(normal_id))
        return normal_id

    def _id_patient(self):
        # parse the external name to get patient ID
        patient_id_raw = self._get_unique_value(self.GEO_EXTERNAL_NAME, check=False)
        return re.split(',', patient_id_raw).pop(0)

    def _id_tumour(self, patient_id):
        self.logger.debug("Finding tumour ID")
        tumour_id = self._id_tumour_normal(patient_id, reference=False)
        self.logger.debug("Found tumour ID: {0}".format(tumour_id))
        return tumour_id

    def _id_tumour_normal(self, patient_id, reference):
        """
        Find the tumour or normal ID -- process differs only by value of the 'reference' flag
        tube ID > group_ID > constructed, in order of preference
        """
        tube_id = self._get_unique_value(self.GEO_TUBE_ID, check=True, reference=reference)
        group_id = self._get_unique_value(self.GEO_GROUP_ID, check=True, reference=reference)
        tissue_origin = self._get_unique_value(self.GEO_TISSUE_ORIGIN_ID, check=True, reference=reference)
        if reference:
            tissue_type = 'R'
        else:
            tissue_type = self._get_unique_value(self.GEO_TISSUE_TYPE_ID, check=True, reference=False)
        constructed_id = "{0}_{1}_{2}".format(patient_id, tissue_origin, tissue_type)
        self.logger.debug("ID candidates: {0}, {1}, {2}".format(tube_id, group_id, constructed_id))
        if tube_id:
            chosen_id = tube_id
        elif group_id:
            msg = "Could not find {0}, using {1} for ID".format(self.GEO_TUBE_ID, self.GEO_GROUP_ID)
            self.logger.warning(msg)
            chosen_id = group_id
        else:
            msg = "Could not find {0} or {1}, constructing alternate ID".format(self.GEO_TUBE_ID, self.GEO_GROUP_ID)
            self.logger.warning(msg)
            chosen_id = ref_constructed_id
        return chosen_id

    def _parse_default(self, workflow, metatype, pattern):
        # get most recent file of given workflow, metatype, and file path pattern
        # self._filter_* functions return an iterator
        iterrows = self._filter_workflow(workflow)
        iterrows = self._filter_metatype(metatype, iterrows)
        iterrows = self._filter_pattern(pattern, iterrows) # metatype usually suffices, but double-check
        try:
            row = self._get_most_recent_row(iterrows)
            path = row[index.FILE_PATH]
        except MissingProvenanceError as err:
            msg = "No provenance records meet filter criteria: Workflow = {0}, ".format(workflow) +\
                  "metatype = {0}, regex = {1}.".format(metatype, pattern)
            self.logger.debug(msg)
            path = None
        return path

    def _parse_row_attributes(self, row):
        """
        Input is a triple of (name, attributes, lims_id) from a provenance row
        Parse the attributes string and return a dictionary
        """
        attrs = {}
        attrs[self.ROOT_SAMPLE_NAME_KEY] = row[0]
        attrs[self.LIMS_ID_KEY] = row[2]
        for entry in re.split(';', row[1]):
            pair = re.split('=', entry)
            if len(pair)!=2:
                msg = "Expected attribute of the form KEY=VALUE, found '{0}'".format(entry)
                self.logger.error(msg)
                raise ValueError(msg)
            attrs[pair[0]] = pair[1]
        self.logger.debug("Found row attributes: {0}".format(attrs))
        return attrs

    def find_analysis_unit(self):
        """
        Find the analysis unit for the final PDF report
        If any component of the analysis unit string is not available, return None
        """
        # defined in CGI-Tools/1-linkNiassa.sh as: ${DONR}_${TORI}_${TYPE}_${UNIT} where:
        # - DONR = donor id (ie. OCT_010118) = self.donor
        # - TORI = tissue origin (geo_tissue_origin)
        # - TYPE = tissue type (geo_tissue_type)
        # - UNIT = group ID
        # In legacy CGI-Tools, UNIT could be overridden from a hard-coded file
        # In Djerba, we instead can override the analysis unit by specifying as an INI parameter
        tissue_origin = self._get_unique_value(self.GEO_TISSUE_ORIGIN_ID, check=True, reference=False)
        tissue_type = self._get_unique_value(self.GEO_TISSUE_TYPE_ID, check=True, reference=False)
        unit = self._get_unique_value(self.GEO_GROUP_ID, check=True, reference=False)
        if tissue_origin and tissue_type and unit:
            analysis_unit = "{0}_{1}_{2}_{3}".format(self.donor, tissue_origin, tissue_type, unit)
        else:
            msg = "Cannot generate analysis unit from inputs: "+\
                "{0}".format([self.donor, tissue_origin, tissue_type, unit])
            self.logger.debug(msg)
            analysis_unit = None
        return analysis_unit

    def find_identifiers(self):
        """
        Find the tumour/normal/patient identifiers from file provenance
        """
        patient_id = self._id_patient()
        if patient_id == None:
            self.logger.debug("Cannot find tumour/normal IDs without patient ID; assigning null values")
            tumour_id = None
            normal_id = None
        else:
            tumour_id = self._id_tumour(patient_id)
            normal_id = self._id_normal(patient_id)
        identifiers = {
            ini.TUMOUR_ID: tumour_id,
            ini.NORMAL_ID: normal_id,
            ini.PATIENT_ID: patient_id
        }
        self.logger.debug("Found identifiers: {0}".format(identifiers))
        return identifiers

    def parse_gep_path(self):
        return self._parse_default('rsem', 'application/octet-stream', '\.results$')

    def parse_maf_path(self):
        suffix = 'filter\.deduped\.realigned\.recalibrated\.mutect2\.filtered\.maf\.gz$'
        return self._parse_default('variantEffectPredictor', 'application/txt-gz', suffix)

    def parse_mavis_path(self):
        return self._parse_default('mavis', 'application/zip-report-bundle', '(mavis-output|summary)\.zip$')

    def parse_sequenza_path(self):
        return self._parse_default('sequenza', 'application/zip-report-bundle', '_results\.zip$')

class MissingConfigError(Exception):
    pass

class MissingProvenanceError(Exception):
    pass
