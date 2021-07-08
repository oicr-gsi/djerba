"""Configure an INI file with Djerba inputs"""

import csv
import gzip
import logging
import os
import re

import djerba.util.constants as constants
import djerba.util.index as index
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
    MUTATION_NONSYN_NAME = 'mutation_types.nonsynonymous'
    GENELIST_NAME = 'targeted_genelist.txt'
    TMBCOMP_NAME = 'tmbcomp.txt'

    # TODO validate that discovered config paths are readable

    def __init__(self, config, validate=True, log_level=logging.WARNING, log_path=None):
        self.config = config
        self.logger = self.get_logger(log_level, __name__, log_path)
        provenance = self.config[ini.SETTINGS][ini.PROVENANCE]
        project = self.config[ini.INPUTS][ini.STUDY_ID]
        donor = self.config[ini.INPUTS][ini.PATIENT]
        try:
            self.reader = provenance_reader(provenance, project, donor, log_level, log_path)
        except MissingProvenanceError as err:
            msg = "Cannot create provenance reader; file provenance updates will be omitted: "+str(err)
            self.logger.warning(msg)
            self.reader = None

    def find_data_files(self):
        data_files = {}
        if self.config[ini.SETTINGS].get(ini.DATA_DIR):
            data_dir = self.config[ini.SETTINGS][ini.DATA_DIR]
        else:
            data_dir = os.path.join(os.path.dirname(__file__), constants.DATA_DIR_NAME)
        data_dir = os.path.realpath(data_dir)
        data_files[ini.ENSCON] = os.path.join(data_dir, self.ENSCON_NAME)
        data_files[ini.ENTCON] = os.path.join(data_dir, self.ENTCON_NAME)
        data_files[ini.GENE_BED] = os.path.join(data_dir, self.GENEBED_NAME)
        data_files[ini.ONCO_LIST] = os.path.join(data_dir, self.ONCOLIST_NAME)
        data_files[ini.MUTATION_NONSYN] = os.path.join(data_dir, self.MUTATION_NONSYN_NAME)
        data_files[ini.GENE_LIST] = os.path.join(data_dir, self.GENELIST_NAME)
        data_files[ini.TMBCOMP] = os.path.join(data_dir, self.TMBCOMP_NAME)
        return data_files

    def discover(self):
        updates = {}
        if self.reader:
            updates[ini.GEP_FILE] = self.reader.parse_gep_path()
            updates[ini.MAF_FILE] = self.reader.parse_maf_path()
            updates[ini.MAVIS_FILE] = self.reader.parse_mavis_path()
            updates[ini.SEQUENZA_FILE] = self.reader.parse_sequenza_path()
        else:
            updates[ini.GEP_FILE] = None
            updates[ini.MAF_FILE] = None
            updates[ini.MAVIS_FILE] = None
            updates[ini.SEQUENZA_FILE] = None
        updates.update(self.find_data_files())
        return updates

    def run(self, out_path):
        """Main method to run configuration"""
        self.update()
        with open(out_path, 'w') as out_file:
            self.config.write(out_file)

    def update(self):
        """Discover and apply updates to the configuration"""
        updates = self.discover()
        if not self.config.has_section(ini.DISCOVERED):
            self.config.add_section(ini.DISCOVERED)
        for key in updates.keys():
            # *do not* overwrite existing params
            # allows user to specify params which will not be overwritten by automated discovery
            if not self.config.has_option(ini.DISCOVERED, key):
                value = updates[key] if updates[key]!=None else ''
                self.config[ini.DISCOVERED][key] = value

class provenance_reader(logger):

    def __init__(self, provenance_path, project, donor,  log_level=logging.WARNING, log_path=None):
        # get provenance for the project and donor
        # if this proves to be too slow, can preprocess the file using zgrep
        self.logger = self.get_logger(log_level, __name__, log_path)
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
            raise MissingProvenanceError(msg)
        return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]

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
                  "metatype = {0}, regex = {1}. ".format(metatype, pattern) +\
                  "(Djerba will run with user-supplied INI params, if available.)"
            self.logger.warning(msg)
            path = None
        return path

    def parse_gep_path(self):
        return self._parse_default('rsem', 'application/octet-stream', '\.results$')

    def parse_maf_path(self):
        suffix = 'filter\.deduped\.realigned\.recalibrated\.mutect2\.filtered\.maf\.gz$'
        return self._parse_default('variantEffectPredictor', 'application/txt-gz', suffix)

    def parse_mavis_path(self):
        return self._parse_default('mavis', 'application/zip-report-bundle', '(mavis-output|summary)\.zip$')

    def parse_sequenza_path(self):
        return self._parse_default('sequenza', 'application/zip-report-bundle', '_results\.zip$')

class MissingProvenanceError(Exception):
    pass
