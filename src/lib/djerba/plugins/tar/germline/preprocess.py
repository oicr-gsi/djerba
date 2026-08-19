"""
Preprocessing for the TAR germline plugin.

  1. stream-filter the germline MAF to the hereditary panel genes
  2. apply germline row filters (depth, VAF, consequence, FILTER)
  3. annotate with OncoKB
  4. derive display columns and split out the oncogenic subset
"""

import csv
import gzip
import logging
import os
import re
import sys

import numpy as np
import pandas as pd

import djerba.core.constants as core_constants
import djerba.plugins.tar.germline.constants as gc
import djerba.util.oncokb.constants as oncokb_constants
from djerba.util.logger import logger
from djerba.util.oncokb.annotator import annotator_factory


class GermlineMafError(Exception):
    """Raised when the input MAF is missing required fields."""


class preprocess(logger):

    def __init__(self, work_dir, config_wrapper, tumour_id, maf_file,
                 log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.log_level = log_level
        self.log_path = log_path
        self.config_wrapper = config_wrapper
        self.tumour_id = tumour_id
        self.maf_file = maf_file
        self.germline_dir = os.path.join(work_dir, gc.GERMLINE_SUBDIR)
        if not os.path.isdir(self.germline_dir):
            os.makedirs(self.germline_dir)

    def run(self):
        """Run the preprocessing steps; return the germline dir."""
        panel_path = os.path.join(self.germline_dir, gc.PANEL_GENES_ONLY)
        filtered_path = os.path.join(self.germline_dir, gc.FILTERED_MAF)
        self.filter_for_panel_genes(self.maf_file, panel_path)
        self.filter_rows(panel_path, filtered_path)
        annotated_path = self.annotate(filtered_path)
        self.write_outputs(annotated_path)
        return self.germline_dir


    # 1. gene filter
    def filter_for_panel_genes(self, maf_path, out_path):
        csv.field_size_limit(sys.maxsize)
        total = 0
        kept = 0
        header = None
        with self._open_maybe_gzip(maf_path) as in_file, \
             open(out_path, 'wt', encoding=core_constants.TEXT_ENCODING,
                  newline='') as out_file:
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t", lineterminator="\n")
            for row in reader:
                if not row:
                    continue
                if header is None:
                    if row[0].startswith('#'):
                        continue
                    header = row
                    gene_indices = self._gene_column_indices(header)
                    writer.writerow(header)
                    continue
                total += 1
                for i in gene_indices:
                    if row[i] in gc.PANEL_GENES:
                        writer.writerow(row)
                        kept += 1
                        break
        if header is None:
            msg = "No header row found in MAF {0}".format(maf_path)
            self.logger.error(msg)
            raise GermlineMafError(msg)
        msg = "Panel gene filter: kept {0} of {1} MAF rows, {2} panel genes"
        self.logger.info(msg.format(kept, total, len(gc.PANEL_GENES)))
        return out_path

    def _gene_column_indices(self, header):
        """ Check both Hugo_Symbol and SYMBOL so a panel gene is never missed. """
        indices = [header.index(k) for k in (gc.HUGO_SYMBOL, gc.SYMBOL)
                   if k in header]
        if not indices:
            msg = "MAF header has neither {0} nor {1}".format(
                gc.HUGO_SYMBOL, gc.SYMBOL)
            self.logger.error(msg)
            raise GermlineMafError(msg)
        return indices

    @staticmethod
    def _open_maybe_gzip(path):
        if re.search(r'\.gz$', path):
            return gzip.open(path, 'rt', encoding=core_constants.TEXT_ENCODING)
        return open(path, 'rt', encoding=core_constants.TEXT_ENCODING)

    # 2. row filter
    def filter_rows(self, in_path, out_path):
        total = 0
        kept = 0
        with open(in_path, encoding=core_constants.TEXT_ENCODING) as in_file, \
             open(out_path, 'wt', encoding=core_constants.TEXT_ENCODING,
                  newline='') as out_file:
            reader = csv.DictReader(in_file, delimiter="\t")
            self._validate_header(reader.fieldnames, in_path)
            writer = csv.DictWriter(out_file, fieldnames=reader.fieldnames,
                                    delimiter="\t", lineterminator="\n")
            writer.writeheader()
            for row in reader:
                total += 1
                if germline_row_ok(row):
                    row[gc.TUMOUR_SAMPLE_BARCODE] = self.tumour_id
                    writer.writerow(row)
                    kept += 1
        msg = "Germline row filter: kept {0} of {1} panel-gene rows"
        self.logger.info(msg.format(kept, total))
        return out_path

    def _validate_header(self, fieldnames, path):
        """Check every required column is present. Extra columns are fine."""
        if fieldnames is None:
            msg = "No header in {0}".format(path)
            self.logger.error(msg)
            raise GermlineMafError(msg)
        missing = [k for k in gc.MAF_REQUIRED_KEYS if k not in fieldnames]
        if missing:
            msg = "MAF {0} is missing required column(s): {1}".format(
                path, ', '.join(missing))
            self.logger.error(msg)
            raise GermlineMafError(msg)

    # 3. OncoKB annotation
    def annotate(self, in_path):
        factory = annotator_factory(self.log_level, self.log_path)
        annotator = factory.get_annotator(self.germline_dir,
                                          self.config_wrapper)
        return annotator.annotate_maf(in_path)

    # 4. derived columns and output
    def write_outputs(self, annotated_path):
        """Add derived columns; write the full and oncogenic variant files."""
        df = pd.read_csv(annotated_path, sep="\t", dtype=str,
                         keep_default_na=False)
        depth = pd.to_numeric(df[gc.T_DEPTH], errors='coerce')
        alt = pd.to_numeric(df[gc.T_ALT_COUNT], errors='coerce').fillna(0)
        df[gc.TUMOUR_VAF] = (alt / depth.replace(0, np.nan)).fillna(0)
        df[gc.CLIN_SIG_DISPLAY] = df[gc.CLIN_SIG].map(format_clin_sig)
        all_path = os.path.join(self.germline_dir, gc.GERMLINE_ALL)
        df.to_csv(all_path, sep="\t", index=False)
        if oncokb_constants.ONCOGENIC_UC in df.columns:
            oncogenic = df[df[oncokb_constants.ONCOGENIC_UC].isin(
                [oncokb_constants.ONCOGENIC, oncokb_constants.LIKELY_ONCOGENIC]
            )]
        else:
            oncogenic = df.iloc[0:0]
        onco_path = os.path.join(self.germline_dir, gc.GERMLINE_ONCOGENIC)
        oncogenic.to_csv(onco_path, sep="\t", index=False)
        msg = "Wrote {0} germline variants, {1} oncogenic"
        self.logger.info(msg.format(len(df), len(oncogenic)))
        return all_path, onco_path


def _to_float(value):
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clin_sig_terms(clin_sig):
    if not clin_sig or clin_sig in ('.', 'NA'):
        return []
    return [t.strip().lower() for t in re.split(r'[,&/|]', clin_sig)
            if t.strip()]


def clin_sig_is_pathogenic(clin_sig):
    """True if ClinVar calls it pathogenic or likely pathogenic."""
    return any(t in gc.CLIN_SIG_PATHOGENIC for t in clin_sig_terms(clin_sig))


def format_clin_sig(clin_sig):
    terms = clin_sig_terms(clin_sig)
    if not terms:
        return 'Not reported'
    return ', '.join(t.replace('_', ' ').capitalize() for t in terms)


def germline_row_ok(row):
    if row.get(gc.FILTER, '') not in gc.FILTER_PASS_VALUES:
        return False
    depth = _to_float(row.get(gc.T_DEPTH))
    alt_count = _to_float(row.get(gc.T_ALT_COUNT))
    if depth < gc.MIN_DEPTH:
        return False
    if alt_count / depth < gc.MIN_VAF_GERMLINE:
        return False
    if row.get(gc.VARIANT_CLASSIFICATION) in gc.GERMLINE_MUTATION_TYPES:
        return True
    # A ClinVar pathogenic call overrides the consequence list, so a
    # deep-intronic or UTR pathogenic allele is not silently dropped.
    return clin_sig_is_pathogenic(row.get(gc.CLIN_SIG, ''))
