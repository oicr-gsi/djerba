"""Read/write a cache of oncoKB results; allows faster, offline access"""

# NOTE: OncoKB annotator takes an 'info' file including the OncoTree code as input
# It is the user's responsibility to ensure cache updates use a consistent OncoTree code
# (Not expected to be an issue for test data with known OncoTree codes)

import csv
import gzip
import hashlib
import json
import logging
import os
import re
from djerba.util.logger import logger
from djerba.util.validator import path_validator
import djerba.extract.oncokb.constants as oncokb_constants
import djerba.util.constants as constants

class oncokb_cache_params(logger):
    """Convenience class to contain parameters for caching operation"""

    def __init__(self, cache_dir=None, apply_cache=False, update_cache=False,
                 log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        # Check cache inputs and configure cache (if any)
        err = None
        if apply_cache and update_cache:
            err = "Bad arguments; cannot do both apply_cache and update_cache for oncoKB caching"
        elif (apply_cache or update_cache) and not cache_dir:
            err = "Bad arguments; apply/update cache requested without cache_dir"
        if err:
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.cache_dir = cache_dir
        self.apply_cache = apply_cache
        self.update_cache = update_cache

    def __str__(self):
        params = {
            'cache_dir': self.cache_dir,
            'apply_cache': self.apply_cache,
            'update_cache': self.update_cache
        }
        return str(params)

    def __repr__(self):
        return self.__str__()

    def get_cache_dir(self):
        return self.cache_dir

    def get_apply_cache(self):
        return self.apply_cache

    def get_update_cache(self):
        return self.update_cache


class oncokb_cache(logger):

    DEFAULT_FUSION_ANNOTATIONS = ['True', 'False', 'False', 'Unknown', '', 'Unknown', '', '', '', '',
                                  '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
    DEFAULT_MAF_ANNOTATIONS = ["True", "False", "False", "Unknown", '', "Unknown", '', '', '', '',
                               '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']

    # headers for extra annotation columns
    ANNOTATION_HEADERS = ["ANNOTATED", "GENE_IN_ONCOKB", "VARIANT_IN_ONCOKB", "MUTATION_EFFECT", "MUTATION_EFFECT_CITATIONS", "ONCOGENIC", "LEVEL_1", "LEVEL_2", "LEVEL_3A", "LEVEL_3B", "LEVEL_4", "LEVEL_R1", "LEVEL_R2", "HIGHEST_LEVEL", "HIGHEST_SENSITIVE_LEVEL", "HIGHEST_RESISTANCE_LEVEL", "TX_CITATIONS", "LEVEL_Dx1", "LEVEL_Dx2", "LEVEL_Dx3", "HIGHEST_DX_LEVEL", "DX_CITATIONS", "LEVEL_Px1", "LEVEL_Px2", "LEVEL_Px3", "HIGHEST_PX_LEVEL", "PX_CITATIONS"]

    def __init__(self, cache_base, oncotree_code=None, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)
        self.validator.validate_output_dir(cache_base)
        # if oncotree_code is given, output to a subdirectory
        # avoids cache collision between same variants with different oncotree code
        if oncotree_code:
            self.cache_dir = os.path.join(cache_base, oncotree_code.lower())
            if os.path.exists(self.cache_dir):
                self.logger.debug('Using existing cache subdirectory {0}'.format(self.cache_dir))
            else:
                os.mkdir(self.cache_dir)
                self.logger.debug('Created cache subdirectory {0}'.format(self.cache_dir))
        else:
            self.cache_dir = cache_base
            self.logger.debug('No OncoTree code given, writing to cache dir {0}'.format(self.cache_dir))
        # individual cache files need not exist at object creation; may be written later
        self.maf_cache = os.path.join(self.cache_dir, oncokb_constants.CACHE_MAF)
        self.cna_cache = os.path.join(self.cache_dir, oncokb_constants.CACHE_CNA)
        self.fusion_cache = os.path.join(self.cache_dir, oncokb_constants.CACHE_FUSION)

    def _initialize_cache(self, cache_input):
        if cache_input:
            with open(cache_input) as cache_file:
                cache = json.loads(cache_file.read())
                msg = "Read {0} annotations from cache file {1}".format(len(cache), cache_input)
                self.logger.debug(msg)
        else:
            cache = {}
            self.logger.debug("No cache input given")
        return cache

    def _make_maf_key(self, row, boundary):
        base = re.sub("[\r\n]", "", "\t".join(row[0:boundary]))
        return hashlib.sha256(base.encode(constants.TEXT_ENCODING)).hexdigest()

    def _open_maybe_gzip(self, input_path):
        if re.search('\.gz$', input_path):
            return gzip.open(input_path, 'rt')
        else:
            return open(input_path)

    def _read_oncokb_info(self, info_path):
        rows = 0
        with open(info_path) as info_file:
            reader = csv.DictReader(info_file, delimiter="\t")
            for row in reader:
                sample = row.get('SAMPLE_ID')
                oncotree_code = row.get('ONCOTREE_CODE')
                rows += 1
        if rows > 1:
            raise RuntimeError("More than one data row in {0}".format(info_path))
        elif sample == None or oncotree_code == None:
            raise RuntimeError("Could not parse sample or oncotree code from {0}".format(info_path))
        return [sample, oncotree_code]

    def _write_cache(self, cache, cache_output):
        with open(cache_output, 'w') as cache_file:
            cache_file.write(json.dumps(cache))
        msg = "Wrote {0} annotations to cache file {1}".format(len(cache), cache_output)
        self.logger.debug(msg)

    def annotate_cna(self, input_cna, output_cna, oncokb_info):
        """
        Annotate a CNA file from the cache
        No defaults supported; all hugo_symbol/alteration pairs must be in the cache
        This is consistent with our practice of only annotating CNAs found in OncoKB
        """
        self.validator.validate_input_file(self.cna_cache)
        msg = "Annotating CNA from cache: "+\
              "Input {0}, output {1}, metadata {2}".format(input_cna, output_cna, oncokb_info)
        self.logger.debug(msg)
        with open(self.cna_cache) as cache_file:
            cache = json.loads(cache_file.read())
        cna_keys = []
        with open(input_cna) as input_file:
            reader = csv.reader(input_file, delimiter="\t")
            first = True
            for row in reader:
                hugo_symbol = row[0]
                if first:
                    keys = ['HUGO_SYMBOL', 'ALTERATION']
                    first = False
                elif int(row[1]) == 2:
                    keys = [hugo_symbol, 'Amplification']
                elif int(row[1]) == -2:
                    keys = [hugo_symbol, 'Deletion']
                else:
                    keys = None
                if keys:
                    cna_keys.append(keys)
        [sample, oncotree_code] = self._read_oncokb_info(oncokb_info)
        with open(output_cna, 'w') as output_file:
            first = True
            for keys in cna_keys:
                [hugo_symbol, alteration] = keys
                if first:
                    row = ['SAMPLE_ID', 'CANCER_TYPE', 'HUGO_SYMBOL', 'ALTERATION']
                    row.extend(self.ANNOTATION_HEADERS)
                    first = False
                else:
                    row = [sample, oncotree_code, hugo_symbol, alteration]
                    try:
                        row.extend(cache[hugo_symbol][alteration])
                    except KeyError as err:
                        msg = "No CNA cache value found for [{0}][{1}]".format(hugo_symbol, alteration)
                        self.logger.error(msg)
                        raise RuntimeError(msg) from err
                print("\t".join(row), file=output_file)
            self.logger.debug("Wrote {0} annotated CNA rows".format(len(keys)))
        self.logger.debug("CNA cache annotation done.")

    def annotate_fusion(self, input_fusion, output_fusion):
        """
        Annotate a fusion file from the cache
        Cache key is the fusion ID (column 1, zero-indexed)
        """
        cache_path = self.fusion_cache
        self.logger.debug("Annotating fusion from cache: Input {0}, output {1}".format(input_fusion, output_fusion))
        self.annotate_maf_or_fusion(
            cache_path, input_fusion, output_fusion, lambda x,i:x[1], self.DEFAULT_FUSION_ANNOTATIONS
        )
        self.logger.debug("Fusion annotation done.")

    def annotate_maf(self, input_maf, output_maf):
        """Annotate a MAF file from the cache"""
        cache_path = self.maf_cache
        self.logger.debug("Annotating MAF from cache: Input {0}, output {1}".format(input_maf, output_maf))
        self.annotate_maf_or_fusion(
            cache_path, input_maf, output_maf, self._make_maf_key, self.DEFAULT_MAF_ANNOTATIONS
        )
        self.logger.debug("MAF cache annotation done.")

    def annotate_maf_or_fusion(self, cache_path, input_path, output_path, key_func, defaults):
        """
        Annotate a MAF or Fusion file from the cache; methods differ only by cache keys and defaults
        """
        self.validator.validate_input_file(cache_path)
        with open(cache_path) as cache_file:
            cache = json.loads(cache_file.read())
        reads_from_cache = 0
        total_reads = 0
        annotated_rows = []
        boundary = None # 0-indexed column of first annotation row; needed for MAF annotation
        with self._open_maybe_gzip(input_path) as input_file:
            reader = csv.reader(input_file, delimiter="\t")
            for row in reader:
                if not boundary:
                    boundary = len(row)
                    row.extend(self.ANNOTATION_HEADERS)
                else:
                    key = key_func(row, boundary)
                    anno = cache.get(key)
                    total_reads += 1
                    if anno:
                        row.extend(anno)
                        reads_from_cache += 1
                    else:
                        row.extend(defaults)
                annotated_rows.append(row)
        self.logger.debug("Found annotation for "+\
                          "{0} of {1} variants".format(reads_from_cache, total_reads))
        with open(output_path, 'w') as output_file:
            # not using csv.writer because it appends extra carriage returns
            for row in annotated_rows:
                print("\t".join(row), file=output_file)

    def update_cache_files(self, report_dir):
        """
        Update all cache files in cache_dir, with input from report_dir
        """
        maf = 'maf'
        cna = 'cna'
        fusion = 'fusion'
        inputs = {
            maf: os.path.join(report_dir, 'tmp', oncokb_constants.ANNOTATED_MAF),
            cna: os.path.join(report_dir, oncokb_constants.DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED),
            fusion: os.path.join(report_dir, oncokb_constants.DATA_FUSIONS_ONCOKB_ANNOTATED)
        }
        outputs = {
            maf: self.maf_cache,
            cna: self.cna_cache,
            fusion: self.fusion_cache
        }
        for input_path in inputs.values():
            if not os.path.exists(input_path):
                msg = "Input file {0} does not exist; ".format(input_path)+\
                      "need to generate report with --no-cleanup option?"
                self.logger.error(msg)
                raise RuntimeError(msg)
        existing = {} # existing cache files, if any
        for key in outputs.keys():
            if os.path.exists(outputs[key]):
                existing[key] = outputs[key]
            else:
                existing[key] = None
        self.write_cna_cache(inputs[cna], outputs[cna], existing[cna])
        self.write_fusion_cache(inputs[fusion], outputs[fusion], existing[fusion])
        self.write_maf_cache(inputs[maf], outputs[maf], existing[maf])

    def write_cna_cache(self, annotated_cna, cache_output=None, cache_input=None):
        """
        CNA annotation prepends the sample ID and oncotree code (from clinical info file)
        Do not cache these; do cache lookup by Hugo_Symbol and CNV status
        """
        self.logger.debug("Writing CNA cache")
        if not cache_output:
            cache_output = self.cna_cache
        if cache_input==None and os.path.exists(cache_output):
            cache_input = cache_output
        cache = self._initialize_cache(cache_input)
        with open(annotated_cna) as cna_file:
            reader = csv.reader(cna_file, delimiter="\t")
            for row in reader:
                hugo_symbol = row[2]
                alteration = row[3]
                if not hugo_symbol in cache:
                    cache[hugo_symbol] = {}
                cache[hugo_symbol][alteration] = row[4:]
        self._write_cache(cache, cache_output)
        return cache_output

    def write_fusion_cache(self, annotated_fusion, cache_output=None, cache_input=None):
        """
        Create/update the cache with annotations from the given fusion file
        cache_output and cache_input may be the same file
        Fusion annotated file includes the sample ID; do not cache this, use fusion ID only
        Fusion ID has old-style "-" separator instead of "::" for consistency with OncoKB inputs
        """
        self.logger.debug("Writing Fusion cache")
        if not cache_output:
            cache_output = self.fusion_cache
        if cache_input==None and os.path.exists(cache_output):
            cache_input = cache_output
        cache = self._initialize_cache(cache_input)
        with open(annotated_fusion) as fusion_file:
            reader = csv.reader(fusion_file, delimiter="\t")
            for row in reader:
                fusion = row[1]
                annotations = row[2:]
                if annotations!=self.DEFAULT_FUSION_ANNOTATIONS:
                    cache[fusion] = annotations
        self._write_cache(cache, cache_output)
        return cache_output

    def write_maf_cache(self, annotated_maf, cache_output=None, cache_input=None):
        """
        Create/update the cache with annotations from the given MAF file
        cache_output and cache_input may be the same file
        """
        self.logger.debug("Updating MAF cache from annotated file {0}".format(annotated_maf))
        if not cache_output:
            cache_output = self.maf_cache
        if cache_input==None and os.path.exists(cache_output):
            cache_input = cache_output
        cache = self._initialize_cache(cache_input)
        boundary = None
        with self._open_maybe_gzip(annotated_maf) as maf_file:
            reader = csv.reader(maf_file, delimiter="\t")
            for row in reader:
                if not boundary: # find annotation start index from the header
                    for i in range(len(row)):
                        if row[i]==self.ANNOTATION_HEADERS[0]:
                            boundary = i
                            break
                    if boundary == None:
                        msg = "Cannot deduce annotation boundary; MAF input file "+\
                              "{0} may have no header and/or not be annotated".format(annotated_maf)
                        self.logger.error(msg)
                        raise RuntimeError(msg)
                else:
                    key = self._make_maf_key(row, boundary)
                    annotations = row[boundary:]
                    if annotations[1] == 'True':
                        cache[key] = annotations
        self._write_cache(cache, cache_output)
        return cache_output
