"""
Ancillary functions for SNV/indel processing
"""

import os
import re
import csv
import gzip
import json
import logging
import djerba.core.constants as core_constants
import djerba.plugins.wgts.snv_indel.constants as sic
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.plugins.cnv import constants as cnv_constants
from djerba.plugins.wgts.tools import wgts_tools
from djerba.util.environment import directory_finder
from djerba.util.html import html_builder
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.oncokb.annotator import annotator_factory
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.oncokb.tools import gene_summary_reader
from djerba.util.subprocess_runner import subprocess_runner

class whizbam:

    """Class to contain a whizbam link method"""

    @staticmethod
    def link_base(whizbam_base_url, studyid, tumourid, normalid, seqtype, genome):
        whizbam = "".join([whizbam_base_url,
                           "/igv?project1=", studyid,
                           "&library1=", tumourid,
                           "&file1=", tumourid, ".bam",
                           "&seqtype1=", seqtype,
                           "&project2=", studyid,
                           "&library2=", normalid,
                           "&file2=", normalid, ".bam",
                           "&seqtype2=", seqtype,
                           "&genome=", genome
        ])
        return whizbam

class snv_indel_processor(logger):

    """Process inputs and write intermediate files to get snv/indel results"""

    def __init__(self, workspace, config_wrapper, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.workspace = workspace
        # TODO update to use workspace object instead of work_dir where possible
        self.work_dir = workspace.get_work_dir()
        self.config = config_wrapper
        self.data_dir = directory_finder(log_level, log_path).get_data_dir()

    def _maf_body_row_ok(self, row, ix, vaf_cutoff):
        """
        Should a MAF row be kept for output?
        Implements logic from functions.sh -> hard_filter_maf() in CGI-Tools
        Expected to filter out >99.9% of input reads
        ix is a dictionary of column indices
        """
        ok = False
        row_t_depth = int(row[ix.get(sic.T_DEPTH)])
        alt_count_raw = row[ix.get(sic.T_ALT_COUNT)]
        gnomad_af_raw = row[ix.get(sic.GNOMAD_AF)]
        row_t_alt_count = float(alt_count_raw) if alt_count_raw!='' else 0.0
        row_gnomad_af = float(gnomad_af_raw) if gnomad_af_raw!='' else 0.0
        is_matched = row[ix.get(sic.MATCHED_NORM_SAMPLE_BARCODE)] != 'unmatched'
        filter_flags = re.split(';', row[ix.get(sic.FILTER)])
        var_class = row[ix.get(sic.VARIANT_CLASSIFICATION)]
        tert_hotspot = self.is_tert_hotspot(row, ix)
        hugo_symbol = row[ix.get(sic.HUGO_SYMBOL)]
        if row_t_depth >= 1 and \
           row_t_alt_count/row_t_depth >= vaf_cutoff and \
           (is_matched or row_gnomad_af < self.MAX_UNMATCHED_GNOMAD_AF) and \
           var_class in sic.MUTATION_TYPES_EXONIC and \
           not any([z in sic.FILTER_FLAGS_EXCLUDE for z in filter_flags]) and \
           not (var_class == "5'Flank" and hugo_symbol != 'TERT'):
            ok = True
            if hugo_symbol == 'TERT' and not tert_hotspot:
                ok = False
        return ok

    def _read_maf_indices(self, row):
        indices = {}
        for i in range(len(row)):
            key = row[i]
            if key in sic.MAF_KEYS:
                indices[key] = i
        if set(indices.keys()) != set(sic.MAF_KEYS):
            msg = "Indices found in MAF header {0} ".format(indices.keys()) +\
                    "do not match required keys {0}".format(sic.MAF_KEYS)
            self.logger.error(msg)
            raise RuntimeError(msg)
        return indices

    def annotate_maf(self, maf_path):
        factory = annotator_factory(self.log_level, self.log_path)
        return factory.get_annotator(self.work_dir, self.config).annotate_maf(maf_path)

    def convert_vaf_plot(self):
        """Read VAF plot from file and return as a base64 string"""
        image_converter = converter(self.log_level, self.log_path)
        plot_path = os.path.join(self.work_dir, sic.VAF_PLOT_FILENAME)
        vaf_plot = image_converter.convert_svg(plot_path, 'CNV plot')
        return vaf_plot

    def get_merge_inputs(self):
        """
        Read gene and therapy information for merge inputs
        Both are derived from the annotated mutations file
        """
        # read the tab-delimited input file
        gene_info = []
        gene_info_factory = gim_factory(self.log_level, self.log_path)
        summaries = gene_summary_reader(self.log_level, self.log_path)
        treatments = []
        treatment_option_factory = tom_factory(self.log_level, self.log_path)
        oncotree_code = self.config.get_my_string(sic.ONCOTREE_CODE)
        with open(os.path.join(self.work_dir, sic.MUTATIONS_ONCOGENIC)) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row_input in reader:
                # record the gene for all reportable alterations
                level = oncokb_levels.parse_oncokb_level(row_input)
                if level not in ['Unknown', 'NA']:
                    gene = row_input[sic.HUGO_SYMBOL]
                    gene_info_entry = gene_info_factory.get_json(
                        gene=gene,
                        summary=summaries.get(gene)
                    )
                    gene_info.append(gene_info_entry)
                therapies = oncokb_levels.parse_actionable_therapies(row_input)
                # record therapy for all actionable alterations (OncoKB level 4 or higher)
                # row may contain therapies at multiple OncoKB levels
                for level in therapies.keys():
                    alt = row_input[sic.HGVSP_SHORT]
                    if gene == 'BRAF' and alt == 'p.V640E':
                        alt = 'p.V600E'
                    alt_url = html_builder.build_alteration_url(gene, alt, oncotree_code)
                    if 'splice' in row_input[sic.VARIANT_CLASSIFICATION].lower():
                        alt = 'p.? (' + row_input[sic.HGVSC] + ')'
                        alt_url = html_builder.build_alteration_url(gene, "Truncating%20Mutations", oncotree_code)
                    if gene == 'TERT':
                        # filtering for TERT hot spot would have already occured so this is a hot spot
                        if row_input[sic.START] == '1295113':
                            alt = 'p.? (c.-124G>A)'
                        elif row_input[sic.START] == '1295135':
                            alt = 'p.? (c.-146G>A)'
                        alt_url = html_builder.build_alteration_url(
                            gene, "Promoter%20Mutation", oncotree_code
                        )
                    treatment_entry = treatment_option_factory.get_json(
                        tier = oncokb_levels.tier(level),
                        level = level,
                        gene = gene,
                        alteration = alt,
                        alteration_url = alt_url,
                        treatments = therapies[level]
                    )
                    treatments.append(treatment_entry)
        # assemble the output
        merge_inputs = {
            'gene_information_merger': gene_info,
            'treatment_options_merger': treatments
        }
        return merge_inputs

    def get_mutation_depth(self, row):
        depth = row['t_depth']
        alt_count = row['t_alt_count']
        return "{0}/{1}".format(alt_count, depth)

    def get_mutation_totals(self):
        # Count the somatic and coding mutations
        # Splice_Region is *excluded* for TMB, *included* in our mutation tables and counts
        # Splice_Region mutations are of interest, but excluded from standard TMB definition
        # The TMB mutation count is (independently) implemented and used in vaf_plot.R
        # See JIRA ticket GCGI-496
        total = 0
        excluded = 0
        with open(os.path.join(self.work_dir, sic.MUTATIONS_ALL)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                total += 1
                if row.get(sic.VARIANT_CLASSIFICATION) in sic.TMB_EXCLUDED:
                    excluded += 1
        coding_total = total - excluded
        msg = "Found {} small mutations and indels, ".format(total)+\
            "of which {} are coding mutations".format(coding_total)
        self.logger.debug(msg)
        return [total, coding_total]

    def get_mutation_type(self, row):
        mutation_type = row[sic.VARIANT_CLASSIFICATION]
        mutation_type = mutation_type.replace('_', ' ')
        return mutation_type

    def get_results(self):
        """Read the R script output into the JSON serializable results structure"""
        self.logger.debug("Collating SNV/indel results for JSON output")
        oncotree_code = self.config.get_my_string(sic.ONCOTREE_CODE)
        rows = []
        wgts_toolkit = wgts_tools(self.log_level, self.log_path)
        is_wgts = wgts_toolkit.has_expression(self.work_dir)
        if is_wgts:
            self.logger.info("Reading expression from {0}".format(self.work_dir))
            expression = wgts_tools.read_expression(self.work_dir)
        else:
            self.logger.info("No expression data found")
            expression = {}
        cytobands = wgts_tools(self.log_level, self.log_path).cytoband_lookup()
        if self.workspace.has_file(cnv_constants.COPY_STATE_FILE):
            has_copy_states = True
            copy_states = self.workspace.read_json(cnv_constants.COPY_STATE_FILE)
        else:
            has_copy_states = False
            copy_states = {}
        with open(os.path.join(self.work_dir, sic.MUTATIONS_ONCOGENIC)) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row_input in reader:
                gene = row_input[sic.HUGO_SYMBOL]
                [protein, protein_url] = self.get_protein_info(row_input, oncotree_code)
                row_output = {
                    wgts_tools.EXPRESSION_PERCENTILE: expression.get(gene), # None for WGS
                    wgts_tools.GENE: gene,
                    wgts_tools.GENE_URL: html_builder.build_gene_url(gene),
                    sic.PROTEIN: protein,
                    sic.PROTEIN_URL: protein_url,
                    sic.TYPE: self.get_mutation_type(row_input),
                    sic.VAF: self.get_tumour_vaf(row_input),
                    sic.DEPTH: self.get_mutation_depth(row_input),
                    sic.COPY_STATE: copy_states.get(gene), # None if copy states not available
                    wgts_tools.CHROMOSOME: cytobands.get(gene, wgts_tools.UNKNOWN),
                    wgts_tools.ONCOKB: oncokb_levels.parse_oncokb_level(row_input)
                }
                rows.append(row_output)
        rows = list(filter(oncokb_levels.oncokb_filter, wgts_toolkit.sort_variant_rows(rows)))
        somatic_total, coding_seq_total = self.get_mutation_totals()
        results = {
            sic.SOMATIC_MUTATIONS: somatic_total,
            sic.CODING_SEQUENCE_MUTATIONS: coding_seq_total,
            sic.ONCOGENIC_MUTATIONS: len(rows),
            sic.VAF_PLOT: self.convert_vaf_plot(),
            sic.HAS_COPY_STATE_DATA: has_copy_states,
            sic.HAS_EXPRESSION_DATA: is_wgts,
            wgts_tools.BODY: rows
        }
        return results

    def get_protein_info(self, row, oncotree_code):
        """Find protein name/URL and apply special cases"""
        gene = row[sic.HUGO_SYMBOL]
        protein = row[sic.HGVSP_SHORT]
        if gene == 'BRAF' and protein == 'p.V640E':
            protein = 'p.V600E'
        protein_url = html_builder.build_alteration_url(gene, protein, oncotree_code)
        if 'splice' in row[sic.VARIANT_CLASSIFICATION].lower():
            protein = 'p.? (' + row[sic.HGVSC] + ')'
            protein_url = html_builder.build_alteration_url(
                gene, "Truncating%20Mutations", oncotree_code
            )
        if gene == 'TERT': 
            # filtering for TERT hot spot would have already occured so this is a hot spot
            if row[sic.START] == '1295113':
                protein = 'p.? (c.-124G>A)'
            elif row[sic.START] == '1295135':
                protein = 'p.? (c.-146G>A)'
            protein_url = html_builder.build_alteration_url(
                gene, "Promoter%20Mutation", oncotree_code
            )
        return [protein, protein_url]

    def get_tumour_vaf(self, row):
        vaf = row['tumour_vaf']
        vaf = int(round(float(vaf), 2)*100)
        return vaf

    def is_tert_hotspot(self, row, ix):
        """
        Hot spots are:
        1. -124 bp (nucleotide polymorphism G > A (chr5, 1295113 assembly GRCh38))
        2. -146 bp (nucleotide polymorphism G > A (chr5, 1295135 assembly GRCh38))
        """
        chromosome = row[ix.get(sic.CHROMOSOME)]
        start = row[ix.get(sic.START)]
        ref_allele = row[ix.get(sic.REF_ALLELE)]
        tum_allele = row[ix.get(sic.TUM_ALLELE)]

        if chromosome == 'chr5' and start in ['1295113', '1295135'] and ref_allele == "G" and tum_allele == "A":
            return True
        else:
            return False

    def preprocess_maf(self, maf_path, tumour_id):
        """Filter a MAF file to remove unwanted rows; also update the tumour ID"""
        tmp_path = os.path.join(self.work_dir, 'filtered_maf.tsv')
        vaf_cutoff = sic.MIN_VAF
        self.logger.info("Filtering MAF input")
        # find the relevant indices on-the-fly from MAF column headers
        # use this instead of csv.DictReader to preserve the rows for output
        with gzip.open(maf_path, 'rt', encoding=core_constants.TEXT_ENCODING) as in_file,\
             open(tmp_path, 'wt') as tmp_file:
            # preprocess the MAF file
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(tmp_file, delimiter="\t")
            in_header = True
            total = 0
            kept = 0
            header_length = 0
            for row in reader:
                if in_header:
                    if re.match('#version', row[0]):
                        # do not write the version header
                        continue
                    else:
                        # write the column headers without change
                        writer.writerow(row)
                        indices = self._read_maf_indices(row)
                        header_length = len(row)
                        in_header = False
                else:
                    total += 1
                    if len(row) != header_length:
                        msg = "Indices found in MAF header are not of same length as rows!"
                        raise RuntimeError(msg)
                    if self._maf_body_row_ok(row, indices, vaf_cutoff):
                        # filter rows in the MAF body and update the tumour_id
                        row[indices.get(sic.TUMOUR_SAMPLE_BARCODE)] = tumour_id
                        writer.writerow(row)
                        kept += 1
        self.logger.info("Kept {0} of {1} MAF data rows".format(kept, total))
        return tmp_path

    def run_data_rscript(self, whizbam_url, maf_input_path):
        dir_location = os.path.dirname(__file__)
        # TODO make the ensembl conversion file specific to this plugin?
        cmd = [
            'Rscript', os.path.join(dir_location, 'R', 'process_snv_data.r'),
            '--basedir', dir_location,
            '--enscon', os.path.join(self.data_dir, sic.ENSEMBL_CONVERSION), 
            '--outdir', self.work_dir,
            '--whizbam_url', whizbam_url,
            '--maffile', maf_input_path
        ]
        runner = subprocess_runner(self.log_level, self.log_path)
        result = runner.run(cmd, "main snv/indel R script")
        return result

    def write_vaf_plot(self):
        """Run the R script to write the VAF plot"""
        dir_location = os.path.dirname(__file__)
        # TODO make the ensembl conversion file specific to this plugin?
        cmd = [
            'Rscript', os.path.join(dir_location, 'R', 'vaf_plot.r'),
            '--dir', self.work_dir,
            '--output', os.path.join(self.work_dir, sic.VAF_PLOT_FILENAME)
        ]
        runner = subprocess_runner(self.log_level, self.log_path)
        result = runner.run(cmd, "VAF plot R script")
        return result

    def whizbam_to_text(self, in_name, out_name):
        in_path = os.path.join(self.work_dir, in_name)
        out_path = os.path.join(self.work_dir, out_name)
        links = []
        with open(in_path) as in_file, open(out_path, 'w') as out_file:
            reader = csv.DictReader(in_file, delimiter="\t")
            writer = csv.DictWriter(
                out_file,
                fieldnames=['Hugo_Symbol', 'whizbam'],
                extrasaction='ignore',
                delimiter="\t"
            )
            writer.writeheader()
            for row in reader:
                writer.writerow(row)

    def write_whizbam_files(self):
        """
        Write Whizbam links in their own files for easier reference
        Original MAF file contains 100+ columns; this is much easier to read
        """
        self.whizbam_to_text(sic.MUTATIONS_ALL, sic.WHIZBAM_ALL)
        self.whizbam_to_text(sic.MUTATIONS_ONCOGENIC, sic.WHIZBAM_ONCOGENIC)
        
    def write_working_files(self, whizbam_url):
        """
        Preprocess inputs, including OncoKB annotation
        Run the main scripts for data processing and VAF plot
        """
        maf_path = self.config.get_my_string(sic.MAF_PATH)
        tumour_id = self.config.get_my_string(sic.TUMOUR_ID)
        maf_path_preprocessed = self.preprocess_maf(maf_path, tumour_id)
        maf_path_annotated = self.annotate_maf(maf_path_preprocessed)
        self.run_data_rscript(whizbam_url, maf_path_annotated)
        self.write_vaf_plot()
        self.write_whizbam_files()
