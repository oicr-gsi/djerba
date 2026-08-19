"""Build the germline plugin results from the annotated variant file."""

import csv
import logging
import os
import re

import djerba.plugins.tar.germline.constants as gc
from djerba.util.html import html_builder as hb
from djerba.util.logger import logger
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.variant_sorter import variant_sorter


class data_builder(logger):

    def __init__(self, germline_dir, oncotree_uc,
                 log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.log_level = log_level
        self.log_path = log_path
        self.germline_dir = germline_dir
        self.oncotree_uc = oncotree_uc

    def build_rows(self):
        """
        Build and sort germline rows, separating reportable variants from
        non-reportable variants for the VUS section.
        """
        variants_file = os.path.join(self.germline_dir, gc.GERMLINE_ALL)
        rows = []
        var_sorter = variant_sorter(self.log_level, self.log_path)
        cytobands = var_sorter.cytoband_lookup()
        with open(variants_file) as data_file:
            for input_row in csv.DictReader(data_file, delimiter="\t"):
                row = self._build_row(input_row, cytobands)
                if row is not None:
                    rows.append(row)
        rows = var_sorter.sort_variant_rows(rows)
        reportable = oncokb_levels.filter_reportable(rows)
        reportable_ids = set(id(r) for r in reportable)
        vus = [r for r in rows if id(r) not in reportable_ids]
        for row in vus:
            if row[gc.ONCOKB] in ('', 'NA', None):
                row[gc.ONCOKB] = 'Unknown'
        return reportable, vus

    def _build_row(self, input_row, cytobands):
        gene = input_row[gc.HUGO_SYMBOL]
        if gene in ('', 'NA', 'None', 'Unknown'):
            return None
        protein = input_row[gc.HGVSP_SHORT]
        is_splice = 'splice' in input_row[gc.VARIANT_CLASSIFICATION].lower()
        if is_splice or not protein:
            # Germline MAFs carry many splice and intronic-adjacent rows with
            # an empty HGVSp_Short; without this the Protein cell renders empty
            # and the OncoKB URL gains a double slash.
            protein = 'p.? ({0})'.format(input_row[gc.HGVSC])
            protein_url = hb.build_alteration_url(
                gene, "Truncating%20Mutations", self.oncotree_uc)
        else:
            protein_url = hb.build_alteration_url(
                gene, protein, self.oncotree_uc)
        vaf = float(input_row[gc.TUMOUR_VAF])
        return {
            gc.GENE: gene,
            gc.GENE_URL: hb.build_gene_url(gene),
            gc.CHROMOSOME: cytobands.get(gene, 'Unknown'),
            gc.PROTEIN: protein,
            gc.PROTEIN_URL: protein_url,
            gc.MUTATION_TYPE: re.sub(
                '_', ' ', input_row[gc.VARIANT_CLASSIFICATION]),
            gc.VAF_PERCENT: int(round(vaf * 100)),
            gc.TUMOUR_DEPTH: int(float(input_row[gc.T_DEPTH] or 0)),
            gc.TUMOUR_ALT_COUNT: int(float(input_row[gc.T_ALT_COUNT] or 0)),
            gc.CLIN_SIG_DISPLAY_KEY: input_row.get(
                gc.CLIN_SIG_DISPLAY) or 'Not reported',
            gc.ONCOKB: oncokb_levels.parse_oncokb_level(input_row),
        }

    def count_total(self):
        """Count germline variants surviving preprocessing."""
        variants_file = os.path.join(self.germline_dir, gc.GERMLINE_ALL)
        total = 0
        with open(variants_file) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                if row[gc.HUGO_SYMBOL] in ('', 'NA', 'None', 'Unknown'):
                    continue
                total += 1
        return total
