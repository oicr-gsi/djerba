"""
Ancillary functions for SNV/indel processing
"""

import os
import re
import csv
import gzip
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import seaborn as sns
import numpy as np
import logging
import djerba.core.constants as core_constants
import djerba.plugins.wgts.cnv_purple.legacy_constants as cnv_constants
import djerba.plugins.wgts.snv_indel.constants as sic
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.util.environment import directory_finder
from djerba.util.html import html_builder
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.oncokb.annotator import annotator_factory
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.oncokb.tools import gene_summary_reader
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.wgts.tools import wgts_tools

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
        biotype = row[ix.get(sic.BIOTYPE)]
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
           biotype == "protein_coding" and \
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

    def add_vaf_to_maf(self, maf_df, alt_col, dep_col, vaf_header):
        # print a warning if any values are missing (shouldn't happen), but change them to 0
        vaf_df = maf_df.copy()
        if vaf_df[alt_col].isna().any() or vaf_df[dep_col].isna().any():
            self.logger.info("Warning! Missing values found in one of the count columns")
            vaf_df[alt_col] = vaf_df[alt_col].fillna(0)
            vaf_df[dep_col] = vaf_df[dep_col].fillna(0)

        # ensure factors end up as numeric
        vaf_df[alt_col] = pd.to_numeric(vaf_df[alt_col])
        vaf_df[dep_col] = pd.to_numeric(vaf_df[dep_col])

        # ensure position comes after alternate count field
        bspot = vaf_df.columns.get_loc(alt_col)
        vaf = pd.Series(vaf_df[alt_col]/vaf_df[dep_col])
        vaf_df.insert(bspot+1, vaf_header, vaf)

        # check for any NAs
        if vaf_df[vaf_header].isna().any():
            self.logger.info("Warning! Missing values found in the new vaf column")
            vaf_df[vaf_header] = vaf_df[vaf_header].fillna(0)

        return vaf_df
    
    def annotate_maf(self, maf_path):
        factory = annotator_factory(self.log_level, self.log_path)
        return factory.get_annotator(self.work_dir, self.config).annotate_maf(maf_path)

    def compute_loh(self, df, cn_file, purity):
        self.logger.info("Computing LOH")
        cn = pd.read_csv(cn_file, sep="\t")
        calc_df = pd.merge(df[["Hugo_Symbol", "tumour_vaf"]], cn, on="Hugo_Symbol")
        calc_df["LHS"] = (calc_df["tumour_vaf"] / float(purity) ) * calc_df["CN"]
        calc_df["RHS"] = calc_df["CN"] - 0.5
        calc_df["LOH"] = (calc_df['LHS'] > calc_df['RHS']) & (calc_df['MACN'] <= 0.5)

        return calc_df

    def construct_whizbam_links(self, df, whizbam_url):
        if not df.empty:
            self.logger.debug("--- adding Whizbam links ---")
            df['whizbam'] = whizbam_url + "&chr=" + df['Chromosome'].str.replace("chr", "") + "&chrloc=" + df['Start_Position'].astype(str) + "-" + df['End_Position'].astype(str)
        else:
            self.logger.debug("--- No Whizbam links added to empty file ---")
        
        return df
    
    def convert_vaf_plot(self):
        """
        Read VAF plot from file if it exists and return as a base64 string
        Else, return False
        """
        image_converter = converter(self.log_level, self.log_path)
        plot_path = os.path.join(self.work_dir, sic.VAF_PLOT_FILENAME)
        if self.workspace.has_file(sic.VAF_PLOT_FILENAME):
            vaf_plot = image_converter.convert_svg(plot_path, 'CNV plot')
        else:
            vaf_plot = None
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
                            alt = 'p.? (c.-124C>T)'
                        elif row_input[sic.START] == '1295135':
                            alt = 'p.? (c.-146C>T)'
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
        if row[sic.HUGO_SYMBOL] == 'TERT':
            mutation_type = 'Promoter'
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
        if self.workspace.has_file(sic.LOH_FILE):
            has_loh = True
            loh_df = pd.read_csv(os.path.join(self.work_dir, sic.LOH_FILE), sep="\t")
            loh_dict = dict(zip(loh_df.Hugo_Symbol, loh_df.LOH))
        else:
            has_loh = False
            loh_dict = {}
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
                    sic.LOH: loh_dict.get(gene), # None of LOH not available
                    wgts_tools.CHROMOSOME: cytobands.get(gene, wgts_tools.UNKNOWN),
                    wgts_tools.ONCOKB: oncokb_levels.parse_oncokb_level(row_input)
                }
                rows.append(row_output)
        rows = wgts_toolkit.sort_variant_rows(rows)
        rows = oncokb_levels.filter_reportable(rows)
        somatic_total, coding_seq_total = self.get_mutation_totals()
        results = {
            sic.SOMATIC_MUTATIONS: somatic_total,
            sic.CODING_SEQUENCE_MUTATIONS: coding_seq_total,
            sic.ONCOGENIC_MUTATIONS: len(rows),
            sic.VAF_PLOT: self.convert_vaf_plot(),
            sic.HAS_LOH_DATA: has_loh,
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
                protein = 'p.? (c.-124C>T)'
            elif row[sic.START] == '1295135':
                protein = 'p.? (c.-146C>T)'
            protein_url = html_builder.build_alteration_url(
                gene, "Promoter%20Mutation", oncotree_code
            )
        return [protein, protein_url]

    def get_tumour_vaf(self, row):
        vaf = row['tumour_vaf']
        vaf = int(round(float(vaf), 2)*100)
        return vaf
    
    def has_somatic_mutations(self):
        """
        Checks if data_mutations_extended.txt is empty.
        This is so we can exclude making a vaf plot if there are no mutations to graph.
        """
        has_somatic_mutations = False
        if self.workspace.has_file(sic.MUTATIONS_ALL):
            df = pd.read_csv(os.path.join(self.work_dir, sic.MUTATIONS_ALL), sep="\t")
            if df.shape[0] != 0: # i.e. there is at least one row present
                has_somatic_mutations = True
        return has_somatic_mutations

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
    
    def proc_vep(self, maf_df):
        # add vaf columns
        vaf_df = self.add_vaf_to_maf(maf_df, alt_col="t_alt_count", dep_col="t_depth", vaf_header="tumour_vaf")
        vaf_df = self.add_vaf_to_maf(vaf_df, alt_col="n_alt_count", dep_col="n_depth", vaf_header="normal_vaf")

        # add oncogenic yes or no columns
        df_anno = vaf_df.copy()
        df_anno['oncogenic_binary'] = np.where(df_anno['ONCOGENIC'].isin(["Oncogenic", "Likely Oncogenic"]), "YES", "NO")

        # add common_variant yes or no columns
        df_anno['ExAC_common'] = np.where(df_anno['FILTER'].str.contains("common_variant"), "YES", "NO")

        # add POPMAX yes or no columns
        gnomad_cols = ["gnomAD_AFR_AF", "gnomAD_AMR_AF", "gnomAD_ASJ_AF", "gnomAD_EAS_AF", "gnomAD_FIN_AF", "gnomAD_NFE_AF", "gnomAD_OTH_AF", "gnomAD_SAS_AF"]
        df_anno[gnomad_cols] = df_anno[gnomad_cols].fillna(0)
        df_anno['gnomAD_AF_POPMAX'] = df_anno[gnomad_cols].max(axis=1)

        # caller artifact filters
        df_anno['FILTER'] = df_anno['FILTER'].replace("^clustered_events$", "PASS", regex=True)
        df_anno['FILTER'] = df_anno['FILTER'].replace("^clustered_events;common_variant$", "PASS", regex=True)
        df_anno['FILTER'] = df_anno['FILTER'].replace("^common_variant$", "PASS", regex=True)
        df_anno['FILTER'] = df_anno['FILTER'].replace(".", "PASS", regex=False)

        # Artifact Filter
        df_anno['TGL_FILTER_ARTIFACT'] = np.where(df_anno['FILTER'] == "PASS", "PASS", "Artifact")

        # ExAC Filter
        df_anno['TGL_FILTER_ExAC'] = np.where((df_anno['ExAC_common'] == "YES") & (df_anno['Matched_Norm_Sample_Barcode'] == "unmatched"), "ExAC_common", "PASS")

        # gnomAD_AF_POPMAX Filter
        df_anno['TGL_FILTER_gnomAD'] = np.where((df_anno['gnomAD_AF_POPMAX'] > 0.001) & (df_anno['Matched_Norm_Sample_Barcode'] == "unmatched"), "gnomAD_common", "PASS")

        # VAF Filter
        df_anno['TGL_FILTER_VAF'] = np.where((df_anno['tumour_vaf'] >= 0.15) | ((df_anno['tumour_vaf'] < 0.15) & (df_anno['oncogenic_binary'] == "YES")), "PASS", "low_VAF")

        # Mark filters
        df_anno['TGL_FILTER_VERDICT'] = np.where((df_anno['TGL_FILTER_ARTIFACT'] == "PASS") & (df_anno['TGL_FILTER_ExAC'] == "PASS") & (df_anno['TGL_FILTER_gnomAD'] == "PASS") & (df_anno['TGL_FILTER_VAF'] == "PASS"), 
                                                 "PASS", 
                                                 df_anno['TGL_FILTER_ARTIFACT'] + ";" + df_anno['TGL_FILTER_ExAC'] + ";" + df_anno['TGL_FILTER_gnomAD'] + ";" + df_anno['TGL_FILTER_VAF'])
        
        df_filt = df_anno[df_anno['TGL_FILTER_VERDICT'] == "PASS"]

        return df_filt

    def process_snv_data(self, whizbam_url, maf_input_path):
        if maf_input_path is None:
            self.logger.info("No MAF file input, processing omitted")
        else:
            self.logger.info("Processing Mutation data")

            # annotate with filters
            self.logger.debug("--- Reading MAF data ---")
            maf_df = pd.read_csv(maf_input_path, sep="\t")

            df_filter = self.proc_vep(maf_df)
            df_filt_whizbam = self.construct_whizbam_links(df=df_filter, whizbam_url=whizbam_url)

            df_filt_whizbam.to_csv(path_or_buf=os.path.join(self.work_dir, "data_mutations_extended.txt"), sep="\t", index=False)

            if df_filter.empty:
                self.logger.info("No passed mutations")
                df_filt_whizbam.to_csv(path_or_buf=os.path.join(self.work_dir, "data_mutations_extended_oncogenic.txt"), sep="\t", index=False)
            else:
                # subset to oncokb annotated genes
                df_filt_oncokb = df_filt_whizbam[(df_filt_whizbam['ONCOGENIC'] == "Oncogenic") | (df_filt_whizbam['ONCOGENIC'] == "Likely Oncogenic")]
                if df_filt_oncokb.empty:
                    self.logger.info("no oncogenic mutations")
                df_filt_oncokb.to_csv(path_or_buf=os.path.join(self.work_dir, "data_mutations_extended_oncogenic.txt"), sep="\t", index=False)

            if self.workspace.has_file("purity_ploidy.json") and self.workspace.has_file("cn.txt"):
                purity = str(self.workspace.read_json("purity_ploidy.json")["purity"])
                cn_file = os.path.join(self.work_dir, "cn.txt")

                final_table = self.compute_loh(df_filt_oncokb, cn_file, purity)
                final_table.to_csv(os.path.join(self.work_dir, "loh.txt"), sep="\t", index=False)
            else:
                self.logger.info("No copy number information, LOH omitted")
   
    def write_vaf_plot(self):
        """"Create VAF plot with matplotlib"""
        data_directory = self.data_dir
        cyto_band = os.path.join(data_directory, 'cytoBand.txt')
        cytoBand = pd.read_csv(cyto_band, sep="\t")

        maf_path = os.path.join(self.work_dir, 'data_mutations_extended.txt')
        output = os.path.join(self.work_dir, sic.VAF_PLOT_FILENAME)
        self.logger.info(f"Creating VAF plot and saving to file {output}")


        MAF = pd.read_csv(maf_path, sep="\t")
        MAF = MAF[~MAF['Variant_Classification'].isin(['Silent', 'Splice_Region'])]
        MAF = MAF.drop(columns=['Chromosome'])
        MAF = MAF.merge(cytoBand, how='inner')
        MAF['OncoKB'] = np.where(MAF['HIGHEST_LEVEL'].isna(), MAF['ONCOGENIC'], MAF['HIGHEST_LEVEL'])
        MAF['tumour_vaf_perc'] = MAF['tumour_vaf'] * 100

        plt.figure(figsize=(7, 1.5))

        sns.kdeplot(data=MAF, 
                    x='tumour_vaf_perc', 
                    fill=True, 
                    color='darkgrey', 
                    alpha=0.5,
                    warn_singular=False
        )
        plt.scatter(MAF['tumour_vaf_perc'], 
                    np.zeros_like(MAF['tumour_vaf_perc']), 
                    color='black', 
                    marker='|',
                    linewidths=0.4)

        plt.xlim(0, 100)
        plt.ylim(0, plt.ylim()[1])
        plt.xlabel("Variant Allele Frequency (%)")
        plt.ylabel("% of mutations")

        plt.gca().set_facecolor('white')
        plt.gca().spines[['top', 'right', 'left', 'bottom']].set_visible(False)
        plt.gca().yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=1))

        plt.grid(False)
        plt.tick_params(left = False, bottom = False)
        plt.xticks([0, 25, 50, 75, 100], fontsize=8)
        plt.yticks(fontsize=8)

        plt.savefig(output, bbox_inches = 'tight', backend='Cairo')

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
        self.process_snv_data(whizbam_url, maf_path_annotated)
        # Exclude the plot if there are no somatic mutations
        if self.has_somatic_mutations():
            self.write_vaf_plot()
        self.write_whizbam_files()
