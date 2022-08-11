"""Class to read and parse the file provenance report (FPR)"""

import csv
import gzip
import logging
import re

import djerba.util.provenance_index as index
import djerba.util.ini_fields as ini
from djerba.util.logger import logger

class provenance_reader(logger):

    # internal dictionary keys
    SAMPLE_NAME_KEY = 'sample_name'

    # parent sample attribute keys
    GEO_EXTERNAL_NAME = 'geo_external_name'
    GEO_GROUP_ID = 'geo_group_id'
    GEO_LIBRARY_SOURCE_TEMPLATE_TYPE = 'geo_library_source_template_type'
    GEO_TISSUE_ORIGIN_ID = 'geo_tissue_origin'
    GEO_TISSUE_TYPE_ID = 'geo_tissue_type'
    GEO_TUBE_ID = 'geo_tube_id'

    # relevant workflow names
    WF_ARRIBA = 'arriba'
    WF_BMPP = 'bamMergePreprocessing'
    WF_DELLY = 'delly'
    WF_MAVIS = 'mavis'
    WF_RSEM = 'rsem'
    WF_SEQUENZA = 'sequenza'
    WF_STAR = 'STAR'
    WF_STARFUSION = 'starFusion'
    WF_VEP = 'variantEffectPredictor'
    RELEVANT_WORKFLOWS = [ # excludes mavis
        WF_ARRIBA,
        WF_BMPP,
        WF_DELLY,
        WF_RSEM,
        WF_STAR,
        WF_VEP,
    ]

    # Includes a concept of 'sample name' (not just 'root sample name')
    # allow user to specify sample names for WG/T, WG/N, WT
    # use to disambiguate multiple samples from the same donor (eg. at different times)
    # sanity checks on FPR results; if not OK, die with an informative error

    # optionally, specify a samples dictionary
    # samples dictionary must list WGT, WGN sample names
    # WTT name may be None (for WG-only reports)
    # if dictionary given, cross check sample names against provenance for consistency
    # otherwise, populate the sample names from provenance (and return to configurer for INI)

    # if conflicting sample names (eg. for different tumour/normal IDs), should fail as it cannot find a unique tumour ID
    # give a more informative error message in this case

    def __init__(self, provenance_path, study, donor, samples=None,
                 log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        # set some constants for convenience
        self.wg_n = ini.SAMPLE_NAME_WG_N
        self.wg_t = ini.SAMPLE_NAME_WG_T
        self.wt_t = ini.SAMPLE_NAME_WT_T
        self.sample_name_keys = [self.wg_n, self.wg_t, self.wt_t]
        # read and parse file provenance
        self.logger.info("Reading provenance for study '%s' and donor '%s' " % (study, donor))
        self.root_sample_name = donor
        self.samples = samples # TODO check samples has correct keys and exactly 0 or 3 values; or convert to a custom class?
        self.logger.info("User-specified sample names: {0}".format(self.samples))
        self.provenance = []
        # find provenance rows with the required study, root sample, and (if given) sample names
        with gzip.open(provenance_path, 'rt') as infile:
            reader = csv.reader(infile, delimiter="\t")
            for row in reader:
                if row[index.STUDY_TITLE] == study and \
                   row[index.ROOT_SAMPLE_NAME] == self.root_sample_name and \
                   (samples==None or row[index.SAMPLE_NAME] in samples.values()) and \
                   row[index.SEQUENCER_RUN_PLATFORM_ID] != 'Illumina_MiSeq':
                    self.provenance.append(row)
        if len(self.provenance)==0:
            # continue with empty provenance results, eg. for GSICAPBENCH testing
            msg = "No provenance records found for study '%s' and donor '%s' " % (study, donor) +\
                "in '%s'" % provenance_path
            self.logger.warning(msg)
            self.attributes = []
            self.patient_id = None
            self.tumour_id = None
            self.normal_id = None
        else:
            self.logger.info("Found %d provenance records" % len(self.provenance))
            self._check_workflows()
            distinct_records = set()
            for row in self.provenance:
                columns = (
                    row[index.SAMPLE_NAME],
                    row[index.PARENT_SAMPLE_ATTRIBUTES]
                )
                distinct_records.add(columns)
            # parse the 'parent sample attributes' value and get a list of dictionaries
            self.attributes = [self._parse_row_attributes(row) for row in distinct_records]
            self._validate_and_set_sample_names(samples)
            self.patient_id = self._id_patient()
            self.tumour_id = self._id_tumour()
            self.normal_id = self._id_normal()

    def _check_workflows(self):
        # check that provenance has all recommended workflows; warn if not
        # this only checks if output exists, *not* if it is correct
        wf_to_check = [ # TODO add Mavis once it is automated
            self.WF_ARRIBA,
            self.WF_BMPP,
            self.WF_DELLY,
            self.WF_RSEM,
            self.WF_STAR,
            self.WF_VEP
        ]
        counts = {key: 0 for key in wf_to_check}
        for row in self.provenance:
            wf = row[index.WORKFLOW_NAME]
            if wf in counts:
                counts[wf] += 1
        for wf in wf_to_check:
            if counts[wf]==0:
                self.logger.warning("No results in file provenance for workflow {0}".format(wf))
            else:
                msg = "Found {0} results in file provenance for workflow {1}".format(counts[wf], wf)
                self.logger.debug(msg)

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
        If check==False, require a unique value across both tumour and normal (eg. to find the patient ID)
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
            value = row.get(key)
            if value:
                value_set.add(value)
            else:
                self.logger.debug("No value found for {0} in {1}".format(key, row))
        self.logger.debug("Candidate value set for key '{0}': {1}".format(key, value_set))
        if len(value_set)==0:
            self.logger.debug("No value found for {0}, reference = {1}".format(key, reference))
            value = None
        elif len(value_set)==1:
            value = list(value_set).pop()
        else:
            msg = "Value for '{0}' with reference={1} is not unique: Found {2}. ".format(key, reference, value_set)
            self.logger.warning(msg)
            value = None
        return value

    def _id_normal(self):
        self.logger.debug("Finding normal ID")
        normal_id = self._id_tumour_normal(self.patient_id, reference=True)
        self.logger.debug("Found normal ID: {0}".format(normal_id))
        return normal_id

    def _id_patient(self):
        # parse the external name to get patient ID
        patient_id_raw = self._get_unique_value(self.GEO_EXTERNAL_NAME, check=False)
        if patient_id_raw == None:
            msg = "Cannot initialize file provenance reader: No value found for metadata field '{0}'".format(self.GEO_EXTERNAL_NAME)
            self.logger.error(msg)
            raise RuntimeError(msg)
        return re.split(',', patient_id_raw).pop(0)

    def _id_tumour(self):
        self.logger.debug("Finding tumour ID")
        tumour_id = self._id_tumour_normal(self.patient_id, reference=False)
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
        if patient_id and tissue_origin and tissue_type:
            constructed_id = "{0}_{1}_{2}".format(patient_id, tissue_origin, tissue_type)
        else:
            constructed_id = None
        self.logger.debug("ID candidates: {0}, {1}, {2}".format(tube_id, group_id, constructed_id))
        if tube_id:
            chosen_id = tube_id
            self.logger.debug("Using {0} value for ID: {1}".format(self.GEO_TUBE_ID, tube_id))
        elif group_id:
            msg = "Could not find {0}, using {1} for ID: {2}".format(self.GEO_TUBE_ID, self.GEO_GROUP_ID, group_id)
            self.logger.warning(msg)
            chosen_id = group_id
        elif constructed_id:
            msg = "Could not find {0} or {1}, constructing alternate ID: {2}".format(self.GEO_TUBE_ID, self.GEO_GROUP_ID, constructed_id)
            self.logger.warning(msg)
            chosen_id = constructed_id
        else:
            msg = "Unable to construct tumour/normal ID for patient ID '{0}'; ".format(patient_id)+\
                  "specifying sample names in INI file may resolve the issue."
            self.logger.error(msg)
            raise RuntimeError(msg)
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
        Input is a (sample name, attributes) pair from a provenance row
        Parse the attributes string and return a dictionary
        """
        attrs = {}
        attrs[self.SAMPLE_NAME_KEY] = row[0]
        for entry in re.split(';', row[1]):
            pair = re.split('=', entry)
            if len(pair)!=2:
                msg = "Expected attribute of the form KEY=VALUE, found '{0}'".format(entry)
                self.logger.error(msg)
                raise ValueError(msg)
            attrs[pair[0]] = pair[1]
        self.logger.debug("Found row attributes: {0}".format(attrs))
        return attrs

    def _validate_and_set_sample_names(self, sample_inputs):
        # find sample names in FPR and check against the inputs dictionary (if any)
        # Firstly, check provenance has exactly one sample for WG/N, WG/T and zero or one for WT/T
        fpr_samples = {key: set() for key in self.sample_name_keys}
        for row in self.attributes:
            if row.get(self.GEO_TISSUE_TYPE_ID)=='R':
                fpr_samples[self.wg_n].add(row.get(self.SAMPLE_NAME_KEY))
            elif row.get(self.GEO_LIBRARY_SOURCE_TEMPLATE_TYPE)=='WG':
                fpr_samples[self.wg_t].add(row.get(self.SAMPLE_NAME_KEY))
            else:
                fpr_samples[self.wt_t].add(row.get(self.SAMPLE_NAME_KEY))
        unique_fpr_samples = {}
        for key in fpr_samples.keys():
            sample_names = fpr_samples.get(key)
            if len(sample_names)==0:
                msg = "No {0} found in provenance".format(key)
                if key==self.wt_t:
                    self.logger.debug(msg)
                    self.logger.debug("Requisition assumed to be whole-genome-only; proceeding")
                    unique_fpr_samples[key] = None
                else:
                    self.logger.error(msg)
                    self.logger.debug("{0} sample is required; exiting".format(key))
                    raise MissingProvenanceError(msg)
            elif len(sample_names)>1:
                msg = "Multiple {0} values found in provenance; ".format(key)+\
                      "candidates are {0}. ".format(sample_names)+\
                      "Setting INI sample name parameters may exclude unwanted values."
                self.logger.error(msg)
                raise ProvenanceConflictError(msg)
            else:
                val = fpr_samples[key].pop()
                self.logger.debug("Found {0} from provenance: {1}".format(key, val))
                unique_fpr_samples[key] = val
        self.logger.info("Consistency check for sample names in file provenance: OK")
        # Secondly, check against the input dictionary (if any)
        if sample_inputs==None:
            self.logger.info("No user-supplied sample names; omitting check against file provenance")
        else:
            for key in self.sample_name_keys:
                # WT sample name in inputs may be None
                if unique_fpr_samples[key] != sample_inputs[key]:
                    msg = "Conflict between {0} sample names: ".format(key)+\
                          "Supplied value = {0}; ".format(sample_inputs[key])+\
                          "Value inferred from file provenance = {0}".format(unique_fpr_samples[key])
                    self.logger.error(msg)
                    raise ProvenanceConflictError(msg)
            self.logger.info("Consistency check between supplied and inferred sample names: OK")
        # Finally, set relevant instance variables
        self.sample_name_wg_n = unique_fpr_samples.get(self.wg_n)
        self.sample_name_wg_t = unique_fpr_samples.get(self.wg_t)
        self.sample_name_wt_t = unique_fpr_samples.get(self.wt_t)

    def get_identifiers(self):
        """
        Get the tumour/normal/patient identifiers, for configuration updates
        """
        identifiers = {
            ini.TUMOUR_ID: self.tumour_id,
            ini.NORMAL_ID: self.normal_id,
            ini.PATIENT_ID: self.patient_id
        }
        self.logger.debug("Got identifiers: {0}".format(identifiers))
        return identifiers

    def get_sample_names(self):
        """
        Get the validated sample names, for configuration updates
        """
        names = {
            ini.SAMPLE_NAME_WG_N: self.sample_name_wg_n,
            ini.SAMPLE_NAME_WG_T: self.sample_name_wg_t,
            ini.SAMPLE_NAME_WT_T: self.sample_name_wt_t
        }
        self.logger.debug("Got sample names: {0}".format(names))
        return names

    def parse_arriba_path(self):
        return self._parse_default(self.WF_ARRIBA, 'application/octet-stream', '\.fusions\.tsv$')

    def parse_delly_path(self):
        return self._parse_default(self.WF_DELLY, 'application/vcf-gz', 'somatic_filtered\.delly\.merged\.vcf\.gz$')

    def parse_gep_path(self):
        return self._parse_default(self.WF_RSEM, 'application/octet-stream', '\.genes\.results$')

    def parse_maf_path(self):
        suffix = 'filter\.deduped\.realigned\.recalibrated\.mutect2\.filtered\.maf\.gz$'
        return self._parse_default(self.WF_VEP, 'application/txt-gz', suffix)

    def parse_mavis_path(self):
        return self._parse_default(self.WF_MAVIS, 'application/zip-report-bundle', '(mavis-output|summary)\.zip$')

    def parse_sequenza_path(self):
        return self._parse_default(self.WF_SEQUENZA, 'application/zip-report-bundle', '_results\.zip$')

    def parse_starfusion_predictions_path(self):
        return self._parse_default(self.WF_STARFUSION, 'application/octet-stream', 'star-fusion\.fusion_predictions\.tsv$')

    def parse_wg_bam_path(self):
        suffix = '{0}\.filter\.deduped\.realigned\.recalibrated\.bam$'.format(self.tumour_id)
        return self._parse_default(self.WF_BMPP, 'application/bam', suffix)

    def parse_wg_bam_ref_path(self):
        # find the reference (normal) BAM
        suffix = '{0}\.filter\.deduped\.realigned\.recalibrated\.bam$'.format(self.normal_id)
        return self._parse_default(self.WF_BMPP, 'application/bam', suffix)

    def parse_wg_index_path(self):
        suffix = '{0}\.filter\.deduped\.realigned\.recalibrated\.bai$'.format(self.tumour_id)
        return self._parse_default(self.WF_BMPP, 'application/bam-index', suffix)

    def parse_wg_index_ref_path(self):
        # find the reference (normal) BAM index
        suffix = '{0}\.filter\.deduped\.realigned\.recalibrated\.bai$'.format(self.normal_id)
        return self._parse_default(self.WF_BMPP, 'application/bam-index', suffix)

    ### WT assay produces only 1 bam file; no need to consider tumour vs. reference

    def parse_wt_bam_path(self):
        # matches *Aligned.sortedByCoord.out.bam if *not* preceded by an index of the form ACGTACGT
        suffix = '('+self.root_sample_name+'.+)((?<![ACGT]{8})\.Aligned)\.sortedByCoord\.out\.bam$'
        return self._parse_default(self.WF_STAR, 'application/bam', suffix)

    def parse_wt_index_path(self):
        # matches *Aligned.sortedByCoord.out.bam if *not* preceded by an index of the form ACGTACGT
        suffix = '('+self.root_sample_name+'.+)((?<![ACGT]{8})\.Aligned)\.sortedByCoord\.out\.bai$'
        return self._parse_default(self.WF_STAR, 'application/bam-index', suffix)

class ProvenanceConflictError(Exception):
    pass

class MissingProvenanceError(Exception):
    pass
