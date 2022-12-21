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
    # temporarily changed to Vidarr versions; TODO allow either Niassa or Vidarr workflow
    WF_ARRIBA = 'arriba'
    WF_BMPP = 'bamMergePreprocessing_by_tumor_group'
    WF_DELLY = 'delly_matched_by_tumor_group'
    WF_MAVIS = 'mavis'
    WF_MSISENSOR = 'msisensor'
    WF_RSEM = 'rsem'
    WF_SEQUENZA = 'sequenza_by_tumor_group'
    WF_STAR = 'star_call_ready'
    WF_STARFUSION = 'starfusion'
    WF_VEP = 'variantEffectPredictor_matched_by_tumor_group'

    # old-style Niassa names (where different)
    NIASSA_WF_BMPP = 'bamMergePreprocessing'
    NIASSA_WF_DELLY = 'delly'
    NIASSA_WF_SEQUENZA = 'sequenza'
    NIASSA_WF_STAR = 'STAR'
    NIASSA_WF_STARFUSION = 'starFusion'
    NIASSA_WF_VEP = 'variantEffectPredictor'

    # metatype patterns
    MT_OCTET_STREAM = 'application/octet-stream$'
    MT_VCF_GZ = 'application/vcf-gz$'
    MT_TXT_GZ = 'application/te?xt-gz$' # match text OR txt
    MT_ZIP = 'application/zip-report-bundle$'
    MT_BAM = 'application/bam$'
    MT_BAM_INDEX = 'application/bam-index$'

    # placeholder
    WT_SAMPLE_NAME_PLACEHOLDER = 'whole_transcriptome_placeholder'

    # Includes a concept of 'sample name' (not just 'root sample name')
    # allow user to specify sample names for WG/T, WG/N, WT
    # use to disambiguate multiple samples from the same donor (eg. at different times)
    # sanity checks on FPR results; if not OK, die with an informative error

    # optionally, input a sample_name_container object
    # if given, cross check input sample names against provenance for consistency
    # otherwise, populate the sample names from provenance (and return to configurer for INI)

    # if conflicting sample names (eg. for different tumour/normal IDs), should fail as it cannot find a unique tumour ID

    def __init__(self, provenance_path, project, donor, samples,
                 log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        # set some constants for convenience
        self.wg_n = ini.SAMPLE_NAME_WG_N
        self.wg_t = ini.SAMPLE_NAME_WG_T
        self.wt_t = ini.SAMPLE_NAME_WT_T
        self.sample_name_keys = [self.wg_n, self.wg_t, self.wt_t]
        # read and parse file provenance
        self.logger.info("Reading provenance for project '%s' and donor '%s' " % (project, donor))
        self.root_sample_name = donor
        if not samples.is_valid():
            msg = "User-supplied sample names are not valid: {0}. ".format(samples)+\
                  "Requires {0} and {1} with optional {2}".format(self.wg_n, self.wg_t, self.wt_t)
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.provenance = []
        # find provenance rows with the required project, root sample, and (if given) sample names
        with gzip.open(provenance_path, 'rt') as infile:
            reader = csv.reader(infile, delimiter="\t")
            for row in reader:
                if row[index.STUDY_TITLE] == project and \
                   row[index.ROOT_SAMPLE_NAME] == self.root_sample_name and \
                   (samples.name_ok(row[index.SAMPLE_NAME])) and \
                   row[index.SEQUENCER_RUN_PLATFORM_ID] != 'Illumina_MiSeq':
                    self.provenance.append(row)
        if len(self.provenance)==0:
            # continue with empty provenance results, eg. for GSICAPBENCH testing
            msg = "No provenance records found for project '%s' and donor '%s' " % (project, donor) +\
                "in '%s'" % provenance_path
            self.logger.warning(msg)
            self._set_empty_provenance()
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
        # check that provenance has all recommended workflows (Niassa or Vidarr); warn if not
        # this only checks if output exists, *not* if it is correct
        wgs_to_check = [
            [self.WF_BMPP, self.NIASSA_WF_BMPP],
            [self.WF_SEQUENZA, self.NIASSA_WF_SEQUENZA],
            [self.WF_VEP, self.NIASSA_WF_VEP]
        ]
        wts_to_check = [ # TODO add Mavis once it is automated
            [self.WF_ARRIBA],
            [self.WF_DELLY, self.NIASSA_WF_DELLY],
            [self.WF_RSEM],
            [self.WF_STAR, self.NIASSA_WF_STAR],
            [self.WF_STARFUSION, self.NIASSA_WF_STARFUSION]
        ]
        counts = {}
        for group in [wgs_to_check, wts_to_check]:
            for wf_list in group:
                for wf in wf_list:
                    counts[wf] = 0
        for row in self.provenance:
            wf = row[index.WORKFLOW_NAME]
            if wf in counts:
                counts[wf] += 1
        self.logger.debug("Beginning check on workflows in file provenance")
        for wf_list in wgs_to_check:
            total = sum([counts[x] for x in wf_list])
            if total==0:
                self.logger.warning("No file provenance records for workflows {0}".format(wf_list))
            else:
                msg = "Found {0} file provenance records for workflows {1}".format(total, wf_list)
                self.logger.debug(msg)
        wts_total = 0
        for wf_list in wts_to_check:
            # first pass -- are there any WTS inputs? None expected for WGS-only report.
            wts_total += sum([counts[x] for x in wf_list])
        if wts_total==0:
            self.logger.debug("No WTS inputs found in file provenance, omitting WTS workflow check")
        else:
            # second pass -- check individual WTS workflows
            for wf_list in wts_to_check:
                total = sum([counts[x] for x in wf_list])
                if sum([counts[x] for x in wf_list])==0:
                    self.logger.warning("No file provenance records for workflows {0}".format(wf_list))
                else:
                    msg = "Found {0} file provenance records for workflows {1}".format(total, wf_list)
                    self.logger.debug(msg)
        self.logger.debug("Finished check on workflows in file provenance")

    def _filter_rows(self, index, value, rows=None):
        # find matching provenance rows from a list
        if rows == None: rows = self.provenance
        return filter(lambda x: x[index]==value, rows)

    def _filter_metatype(self, pattern, rows=None):
        if rows == None: rows = self.provenance
        return filter(lambda x: re.search(pattern, x[index.FILE_META_TYPE]), rows)

    def _filter_file_path(self, pattern, rows=None):
        if rows == None: rows = self.provenance
        return filter(lambda x: re.search(pattern, x[index.FILE_PATH]), rows)

    def _filter_sample_name(self, sample_name, rows=None):
        return self._filter_rows(index.SAMPLE_NAME, sample_name, rows)

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
                  "possible missing/incorrect sample name inputs."
            self.logger.error(msg)
            raise UnknownTumorNormalIDError(msg)
        return chosen_id

    def _parse_multiple_workflows(self, workflows, metatype, pattern, sample_name):
        # Look for file with each workflow name in the list; if file is found, then stop
        # TODO this is to handle Niassa->Vidarr name changes, can later be removed
        for workflow in workflows:
            path = self._parse_file_path(workflow, metatype, pattern, sample_name)
            if path:
                break
        return path

    def _parse_file_path(self, workflow, meta_pattern, file_pattern, sample_name):
        # get most recent file of given workflow, metatype, file path pattern, and sample name
        # self._filter_* functions return an iterator
        iterrows = self._filter_workflow(workflow)
        iterrows = self._filter_metatype(meta_pattern, iterrows)
        iterrows = self._filter_file_path(file_pattern, iterrows)
        iterrows = self._filter_sample_name(sample_name, iterrows)
        try:
            row = self._get_most_recent_row(iterrows)
            path = row[index.FILE_PATH]
        except MissingProvenanceError as err:
            msg = "No provenance records meet filter criteria: Workflow = {0}, ".format(workflow) +\
                  "metatype-regex = {0}, path-regex = {1}.".format(meta_pattern, file_pattern)
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

    def _set_empty_provenance(self):
        # special case for empty file provenance result
        # - all reader attributes are null/empty
        # - can proceed if and only if a fully-specified config is input
        self.attributes = []
        self.patient_id = None
        self.tumour_id = None
        self.normal_id = None
        self.sample_name_wg_n = None
        self.sample_name_wg_t = None
        self.sample_name_wt_t = None

    def _validate_and_set_sample_names(self, sample_inputs):
        # find sample names in FPR and check against the inputs dictionary (if any)
        # Firstly, check provenance has exactly one sample for WG/N, WG/T and zero or one for WT/T
        fpr_samples = sample_name_container()
        for row in self.attributes:
            try:
                if row.get(self.GEO_TISSUE_TYPE_ID)=='R':
                    fpr_samples.set_wg_n(row.get(self.SAMPLE_NAME_KEY))
                elif row.get(self.GEO_LIBRARY_SOURCE_TEMPLATE_TYPE)=='WG':
                    fpr_samples.set_wg_t(row.get(self.SAMPLE_NAME_KEY))
                elif row.get(self.GEO_LIBRARY_SOURCE_TEMPLATE_TYPE)=='WT':
                    fpr_samples.set_wt_t(row.get(self.SAMPLE_NAME_KEY))
                else:
                    msg = "Cannot resolve sample type from row attributes: {0}".format(row)
                    self.logger.error(msg)
                    raise SampleUnknownTypeError(msg)
            except SampleNameOverwriteError as err:
                msg = "Inconsistent sample names found in file provenance: {0}".format(err)
                self.logger.error(msg)
                raise RuntimeError(msg) from err
        if not fpr_samples.has_wg_names():
            msg = "Samples found in file provenance are not sufficient to proceed; requires "+\
                  "WG_N, WG_T, and optionally WT_T; found {0}. ".format(fpr_samples)
            if sample_inputs.is_empty():
                msg += "No restrictions on sample names specified in user input."
            else:
                msg += "Permitted sample names from user input: {0}".format(sample_inputs)
            self.logger.error(msg)
            raise InsufficientSampleNamesError(msg)
        self.logger.info("Consistency check for sample names in file provenance: OK")
        # Secondly, check against the input dictionary (if any)
        if sample_inputs.is_empty():
            self.logger.info("No user-supplied sample names; omitting check")
        elif sample_inputs.is_equal(fpr_samples):
            self.logger.info("Consistency check between supplied and inferred sample names: OK")
        else:
            msg = "Conflicting sample names: {0} from file provenance, ".format(fpr_samples)+\
                  "{1} from user input. ".format(sample_inputs)+\
                  "If INI config has user-supplied sample names, check they are correct."
            self.logger.error(msg)
            raise SampleNameConflictError(msg)
        # Finally, set relevant instance variables
        self.sample_name_wg_n = fpr_samples.get(self.wg_n)
        self.sample_name_wg_t = fpr_samples.get(self.wg_t)
        # WT sample name is optional for WG-only reports, but must be non-null
        wt = fpr_samples.get(self.wt_t)
        self.sample_name_wt_t = wt if wt else self.WT_SAMPLE_NAME_PLACEHOLDER

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

    # Methods to parse file paths for particular workflows
    # If workflow names differ, try Vidarr first, then Niassa

    def parse_arriba_path(self):
        workflow = self.WF_ARRIBA
        mt = self.MT_OCTET_STREAM
        suffix = '\.fusions\.tsv$'
        return self._parse_file_path(workflow, mt, suffix, self.sample_name_wt_t)

    def parse_delly_path(self):
        workflows = [self.WF_DELLY, self.NIASSA_WF_DELLY]
        mt = self.MT_VCF_GZ
        suffix = '\.somatic_filtered\.delly\.merged\.vcf\.gz$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wg_t)

    def parse_gep_path(self):
        workflow = self.WF_RSEM
        mt = self.MT_OCTET_STREAM
        suffix = '\.genes\.results$'
        return self._parse_file_path(workflow, mt, suffix, self.sample_name_wt_t)

    def parse_maf_path(self):
        workflows = [self.WF_VEP, self.NIASSA_WF_VEP]
        mt = self.MT_TXT_GZ
        suffix = '\.filter\.deduped\.realigned\.recalibrated\.mutect2\.filtered\.maf\.gz$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wg_t)

    def parse_mavis_path(self):
        workflow = self.WF_MAVIS
        mt = self.MT_ZIP
        suffix = '(mavis-output|summary)\.zip$'
        return self._parse_file_path(workflow, mt, suffix, self.sample_name_wt_t)

    def parse_sequenza_path(self):
        workflows = [self.WF_SEQUENZA, self.NIASSA_WF_SEQUENZA]
        mt = self.MT_ZIP
        suffix = '_results\.zip$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wg_t)

    def parse_msi_path(self):
        workflows = [self.WF_MSISENSOR]
        mt = self.MT_OCTET_STREAM
        suffix = 'filter\.deduped\.realigned\.recalibrated\.msi\.booted$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wg_t)

    def parse_starfusion_predictions_path(self):
        workflows = [self.WF_STARFUSION, self.NIASSA_WF_STARFUSION]
        mt = self.MT_OCTET_STREAM
        suffix = 'star-fusion\.fusion_predictions\.tsv$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wt_t)

    def parse_wg_bam_path(self):
        workflows = [self.WF_BMPP, self.NIASSA_WF_BMPP]
        mt = self.MT_BAM
        suffix = '\.filter\.deduped\.realigned\.recalibrated\.bam$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wg_t)

    def parse_wg_bam_ref_path(self):
        # find the reference (normal) BAM
        workflows = [self.WF_BMPP, self.NIASSA_WF_BMPP]
        mt = self.MT_BAM
        suffix = '\.filter\.deduped\.realigned\.recalibrated\.bam$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wg_n)

    def parse_wg_index_path(self):
        workflows = [self.WF_BMPP, self.NIASSA_WF_BMPP]
        mt = self.MT_BAM_INDEX
        suffix = '\.filter\.deduped\.realigned\.recalibrated\.bai$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wg_t)

    def parse_wg_index_ref_path(self):
        # find the reference (normal) BAM index
        workflows = [self.WF_BMPP, self.NIASSA_WF_BMPP]
        mt = self.MT_BAM_INDEX
        suffix = '\.filter\.deduped\.realigned\.recalibrated\.bai$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wg_n)

    ### WT assay produces only 1 bam file; no need to consider tumour vs. reference

    def parse_wt_bam_path(self):
        # matches *Aligned.sortedByCoord.out.bam if *not* preceded by an index of the form ACGTACGT
        workflows = [self.WF_STAR, self.NIASSA_WF_STAR]
        mt = self.MT_BAM
        suffix = '('+self.root_sample_name+'.+)((?<![ACGT]{8})\.Aligned)\.sortedByCoord\.out\.bam$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wt_t)

    def parse_wt_index_path(self):
        # matches *Aligned.sortedByCoord.out.bam if *not* preceded by an index of the form ACGTACGT
        workflows = [self.WF_STAR, self.NIASSA_WF_STAR]
        mt = self.MT_BAM_INDEX
        suffix = '('+self.root_sample_name+'.+)((?<![ACGT]{8})\.Aligned)\.sortedByCoord\.out\.bai$'
        return self._parse_multiple_workflows(workflows, mt, suffix, self.sample_name_wt_t)

class sample_name_container:
    """
    Wrapper for a dictionary of sample names
    Contains extra validation and convenience methods
    """

    def __init__(self):
        self.samples = {
            ini.SAMPLE_NAME_WG_N: None,
            ini.SAMPLE_NAME_WG_T: None,
            ini.SAMPLE_NAME_WT_T: None
        }

    def __str__(self):
        return "{0}".format(self.samples)

    def _set_value(self, key, value):
        if self.samples[key]==None or self.samples[key]==value:
            self.samples[key] = value
        else:
            msg = "Cannot overwrite existing {0} value {1} ".format(key, self.samples[key])+\
                  "with new value {0}".format(value)
            raise SampleNameOverwriteError(msg)

    def get(self, key):
        return self.samples[key]

    def is_equal(self, other):
        return all([self.get(key)==other.get(key) for key in self.samples.keys()])

    def is_empty(self):
        return all([x==None for x in self.samples.values()])

    def has_wg_names(self):
        # a ready container has WG tumour and normal sample names; WT sample name is optional
        return self.samples[ini.SAMPLE_NAME_WG_N]!=None and self.samples[ini.SAMPLE_NAME_WG_T]!=None

    def is_valid(self):
        # is the container in a valid state?
        return self.is_empty() or self.has_wg_names()

    def name_ok(self, name):
        return self.is_empty() or name in self.samples.values()

    def set_and_validate(self, wg_n, wg_t, wt_t):
        self.set_wg_n(wg_n)
        self.set_wg_t(wg_t)
        self.set_wt_t(wt_t)
        if not self.is_valid():
            msg = "Failed to configure container for sample names; "+\
                  "requires WG/N, WG/T, and optionally WT/T; "+\
                  "found {0}".format(self.samples)
            raise InvalidConfigurationError(msg)

    def set_wg_n(self, value):
        self._set_value(ini.SAMPLE_NAME_WG_N, value)

    def set_wg_t(self, value):
        self._set_value(ini.SAMPLE_NAME_WG_T, value)

    def set_wt_t(self, value):
        self._set_value(ini.SAMPLE_NAME_WT_T, value)

class InsufficientSampleNamesError(Exception):
    pass

class InvalidConfigurationError(Exception):
    pass

class MissingProvenanceError(Exception):
    pass

class SampleNameConflictError(Exception):
    pass

class SampleNameOverwriteError(Exception):
    pass

class SampleUnknownTypeError(Exception):
    pass

class UnknownTumorNormalIDError(Exception):
    pass
