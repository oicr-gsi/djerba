"""Search for Djerba inputs"""

import csv
import gzip
import os
import re

import djerba.util.constants as constants
import djerba.util.index as index
import djerba.util.ini_fields as ini

class configurer:
    """Class to do configuration in main Djerba method"""

    # TODO validate that discovered config paths are readable

    def __init__(self, config, validate=True):
        self.config = config

    def run(out_path):
        updater = config_updater(self.config)
        updater.update()
        new_config = updater.get_config()
        with open(out_path, 'w') as out_file:
            new_config.write(out_file)

class config_updater:
    """
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

    def __init__(self, config):
        self.config = config
        provenance = self.config[ini.SETTINGS][ini.PROVENANCE]
        project = self.config[ini.INPUTS][ini.STUDY_ID]
        donor = self.config[ini.INPUTS][ini.PATIENT]
        self.reader = provenance_reader(provenance, project, donor)

    def find_data_files(self):
        data_files = {}
        if self.config[ini.SETTINGS].get(ini.DATA_DIR):
            data_dir = self.config[ini.SETTINGS][ini.DATA_DIR]
        else:
            data_dir = os.path.join(os.path.dirname(__file__), '..', constants.DATA_DIR_NAME)
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
        # TODO
        # - get file paths from provenance
        # - get data file paths from data dir, eg. enscon, gep reference
        # - check if all data files are needed (some may be obsolete)
        # - verify all discovered files exist and are readable
        updates[ini.MAF_FILE] = self.reader.parse_maf_path()
        updates[ini.SEQUENZA_FILE] = self.reader.parse_sequenza_path()
        updates.update(self.find_data_files())
        return updates

    def get_config(self):
        return self.config

    def update(self):
        """Input a ConfigParser; discover and apply updates"""
        updates = self.discover()
        if not self.config.has_section(ini.DISCOVERED):
            self.config.add_section(ini.DISCOVERED)
        for key in updates.keys():
            # Overwrite existing params, if any
            self.config[ini.DISCOVERED][key] = updates[key]

class provenance_reader:

    def __init__(self, provenance_path, project, donor):
        # get provenance for the project and donor
        # if this proves to be too slow, can preprocess the file using zgrep
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
            raise MissingProvenanceError("No provenance records found")
        return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]

    def _parse_default(self, workflow, metatype, pattern):
        # get most recent file of given workflow, metatype, and file path pattern
        rows = self._filter_workflow(workflow)
        rows = self._filter_metatype(metatype, rows)
        rows = self._filter_pattern(pattern, rows) # metatype usually suffices, but double-check
        row = self._get_most_recent_row(rows)
        return row[index.FILE_PATH]

    def parse_maf_path(self):
        return self._parse_default('variantEffectPredictor', 'application/txt-gz', '\.maf\.gz$')

    def parse_sequenza_path(self):
        return self._parse_default('sequenza', 'application/zip-report-bundle', '_results\.zip$')

class MissingProvenanceError(Exception):
    pass
