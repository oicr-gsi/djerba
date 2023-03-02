#! /usr/bin/env python3

"""Read a Djerba 'report' directory and generate JSON for the Mako template"""

import base64
import csv
import json
import logging
import os
import re
import pandas as pd
import djerba.extract.oncokb.constants as oncokb
import djerba.extract.constants as xc
import djerba.render.constants as rc
import djerba.util.constants as dc
from djerba import __version__
from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner
from djerba.extract.oncokb.annotator import oncokb_annotator
from statsmodels.distributions.empirical_distribution import ECDF
from djerba.util.image_to_base64 import converter
import djerba.util.ini_fields as ini

class composer_base(logger):
    # base class with shared methods and constants

    NA = 'NA'
    ONCOGENIC = 'ONCOGENIC'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        # list to determine sort order of oncokb level outputs
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.oncokb_levels = [self.reformat_level_string(level) for level in oncokb.ORDERED_LEVELS]
        self.likely_oncogenic_sort_order = self.oncokb_sort_order(oncokb.LIKELY_ONCOGENIC)

    def is_null_string(self, value):
        if isinstance(value, str):
            return value in ['', self.NA]
        else:
            msg = "Invalid argument to is_null_string(): '{0}' of type '{1}'".format(value, type(value))
            self.logger.error(msg)
            raise RuntimeError(msg)

    def oncokb_filter(self, row):
        """True if level passes filter, ie. if row should be kept"""
        return self.oncokb_sort_order(row.get(rc.ONCOKB)) <= self.likely_oncogenic_sort_order

    def oncokb_sort_order(self, level):
        order = None
        i = 0
        for output_level in self.oncokb_levels:
            if level == output_level:
                order = i
                break
            i+=1
        if order == None:
            self.logger.warning(
                "Unknown OncoKB level '{0}'; known levels are {1}".format(level, self.oncokb_levels)
            )
            order = len(self.oncokb_levels)+1 # unknown levels go last
        return order

    def parse_max_oncokb_level_and_therapies(self, row_dict, levels):
        # find maximum level (if any) from given levels list, and associated therapies
        max_level = None
        therapies = []
        for level in levels:
            if not self.is_null_string(row_dict[level]):
                if not max_level: max_level = level
                therapies.append(row_dict[level])
        if max_level:
            max_level = self.reformat_level_string(max_level)
        # insert a space between comma and start of next word
        therapies = [re.sub(r'(?<=[,])(?=[^\s])', r' ', t) for t in therapies]
        return (max_level, '; '.join(therapies))

    def parse_oncokb_level(self, row_dict):
        # find oncokb level string: eg. "Level 1", "Likely Oncogenic", "None"
        max_level = None
        for level in oncokb.THERAPY_LEVELS:
            if not self.is_null_string(row_dict[level]):
                max_level = level
                break
        if max_level:
            parsed_level = self.reformat_level_string(max_level)
        elif not self.is_null_string(row_dict[self.ONCOGENIC]):
            parsed_level = row_dict[self.ONCOGENIC]
        else:
            parsed_level = self.NA
        return parsed_level

    def reformat_level_string(self, level):
        return re.sub('LEVEL_', 'Level ', level)

class clinical_report_json_composer(composer_base):

    ALTERATION_UPPER_CASE = 'ALTERATION'
    ALL_CURATED_GENES = '20201126-allCuratedGenes.tsv'
    CANCER_TYPE_HEADER = 'CANCER.TYPE' # for tmbcomp files
    COMPASS = 'COMPASS'
    CYTOBAND = 'cytoBand.txt'
    DATA_SEGMENTS = 'data_segments.txt'
    EXPR_PCT_TCGA = 'data_expression_percentile_tcga.txt'
    GENOME_SIZE = 3*10**9 # TODO use more accurate value when we release a new report format
    GENOMIC_BIOMARKERS = 'genomic_biomarkers.maf'
    HGVSP_SHORT = 'HGVSp_Short'
    HUGO_SYMBOL_TITLE_CASE = 'Hugo_Symbol'
    HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
    MINIMUM_MAGNITUDE_SEG_MEAN = 0.2
    MSS_CUTOFF = 5.0
    MSI_CUTOFF = 15.0
    MSI_FILE = 'msi.txt'
    MUTATIONS_EXTENDED_ONCOGENIC = 'data_mutations_extended_oncogenic.txt'
    MUTATIONS_EXTENDED = 'data_mutations_extended.txt'
    CNA_ANNOTATED = 'data_CNA_oncoKBgenes_nonDiploid_annotated.txt'
    CNA_ARATIO = 'data_CNA_oncoKBgenes_ARatio.txt'
    CNA_SIMPLE = 'data_CNA.txt'
    BIOMARKERS_ANNOTATED = 'annotated_maf_tmp.tsv'
    INTRAGENIC = 'intragenic'
    ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
    FDA_APPROVED = 'FDA_APPROVED'
    INVESTIGATIONAL = 'INVESTIGATIONAL'
    PAN_CANCER_COHORT = 'TCGA Pan-Cancer Atlas 2018 (n=6,446)'
    TMB_HEADER = 'tmb' # for tmbcomp files
    TMBCOMP_EXTERNAL = 'tmbcomp-externaldata.txt'
    TMBCOMP_TCGA = 'tmbcomp-tcga.txt'
    TUMOUR_VAF = 'tumour_vaf'
    UNKNOWN = 'Unknown'
    VARIANT_CLASSIFICATION = 'Variant_Classification'
    V7_TARGET_SIZE = 37.285536 # inherited from CGI-Tools


    # variant classifications excluded from TMB count
    TMB_EXCLUDED = [
        "3'Flank",
        "3'UTR",
        "5'Flank",
        "5'UTR",
        "Silent",
        "Splice_Region",
        "Targeted_Region",
    ]

    UNCLASSIFIED_CYTOBANDS = [
        "", # some genes have an empty string for cytoband
        "mitochondria",
        "not on reference assembly",
        "reserved",
        "unplaced",
        "13cen",
        "13cen, GRCh38 novel patch",
        "2cen-q11",
        "2cen-q13",
        "c10_B",
        "HSCHR6_MHC_COXp21.32",
        "HSCHR6_MHC_COXp21.33",
        "HSCHR6_MHC_COXp22.1",
        "Unknown"
    ]

    def __init__(self, config, input_dir, params, log_level=logging.WARNING, log_path=None):
        super().__init__(log_level, log_path) # calls the parent constructor; creates logger
        self.config = config
        self.log_level = log_level
        self.log_path = log_path
        self.all_reported_variants = set()
        self.input_dir = input_dir
        self.params = params
        # evaluate the assay type
        permitted = [rc.ASSAY_WGS, rc.ASSAY_WGTS]
        if not self.params.get(xc.ASSAY_TYPE) in permitted:
            msg = "Assay type {0} not in permitted assays {1}".format(assay_type, permitted)
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.is_wgts = self.params.get(xc.ASSAY_TYPE) == rc.ASSAY_WGTS
        # set other instance variables
        self.failed = self.params.get(xc.FAILED)
        self.clinical_data = self.read_clinical_data()
        self.closest_tcga_lc = self.clinical_data[dc.CLOSEST_TCGA].lower()
        self.oncotree_uc = self.params.get(xc.ONCOTREE_CODE).upper()
        self.data_dir = os.path.join(os.environ['DJERBA_BASE_DIR'], dc.DATA_DIR_NAME)
        self.r_script_dir = os.path.join(os.environ['DJERBA_BASE_DIR'], 'R_plots')
        self.html_dir = os.path.join(os.path.dirname(__file__), '..', 'html')
        self.cytoband_path = os.path.join(self.data_dir, 'cytoBand.txt')
        self.cytoband_map = self.read_cytoband_map()
        if self.failed:
            self.total_somatic_mutations = None
            self.tmb_count = None
            self.total_fusion_genes = None
            self.gene_pair_fusions = None
        else:
            [self.total_somatic_mutations, self.tmb_count] = self.read_somatic_mutation_totals()
            if self.is_wgts:
                fus_reader = fusion_reader(input_dir, log_level=log_level, log_path=log_path)
                self.total_fusion_genes = fus_reader.get_total_fusion_genes()
                self.gene_pair_fusions = fus_reader.get_fusions()
                self.expr_input = self.EXPR_PCT_TCGA
            else:
                self.total_fusion_genes = None
                self.gene_pair_fusions = None
                self.expr_input = None


    def build_assay_name(self):
        ##WGS v WGTS
        assay_type = self.params.get(xc.ASSAY_TYPE)
        if assay_type == rc.ASSAY_WGS:
            assay_type_name = "Whole genome sequencing (WGS)-"
        elif assay_type == rc.ASSAY_WGTS:
            assay_type_name = "Whole genome and transcriptome sequencing (WGTS)-"
        ##target
        coverage = self.params.get(xc.COVERAGE)
        if coverage == 40:
            assay_coverage_name = "40X Tumour, 30X Normal "
        elif coverage == 80:
            assay_coverage_name = "80X Tumour, 30X Normal "
        else:
            raise RuntimeError("Unknown depth of coverage")
        ##assay version
        assay_version = self.config[ini.SETTINGS][ini.ASSAY_VERSION]
        assay_version_name = "(v"+assay_version+")"
        assay_name = assay_type_name + assay_coverage_name + assay_version_name
        return(assay_name)

    def build_alteration_url(self, gene, alteration, cancer_code):
        self.logger.debug('Constructing alteration URL from inputs: {0}'.format([self.ONCOKB_URL_BASE, gene, alteration, cancer_code]))
        return '/'.join([self.ONCOKB_URL_BASE, gene, alteration, cancer_code])

    def build_copy_number_variation(self):
        self.logger.debug("Building data for copy number variation table")
        rows = []
        if self.is_wgts:
            mutation_expression = self.read_expression()
        else:
            mutation_expression = {}
        with open(os.path.join(self.input_dir, self.CNA_ANNOTATED)) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                gene = row[self.HUGO_SYMBOL_UPPER_CASE]
                cytoband = self.get_cytoband(gene)
                row = {
                    rc.EXPRESSION_METRIC: mutation_expression.get(gene), # None for WGS assay
                    rc.GENE: gene,
                    rc.GENE_URL: self.build_gene_url(gene),
                    rc.ALT: row[self.ALTERATION_UPPER_CASE],
                    rc.CHROMOSOME: cytoband,
                    rc.ONCOKB: self.parse_oncokb_level(row)
                }
                rows.append(row)
        unfiltered_cnv_total = len(rows)
        self.logger.debug("Sorting and filtering CNV rows")
        rows = list(filter(self.oncokb_filter, self.sort_variant_rows(rows)))
        for row in rows: self.all_reported_variants.add((row.get(rc.GENE), row.get(rc.CHROMOSOME)))
        data = {
            rc.HAS_EXPRESSION_DATA: self.is_wgts,
            rc.TOTAL_VARIANTS: unfiltered_cnv_total,
            rc.CLINICALLY_RELEVANT_VARIANTS: len(rows),
            rc.BODY: rows
        }
        return data

    def build_coverage_thresholds(self):
        coverage_thresholds = {
            rc.NORMAL_MIN: 30,
            rc.NORMAL_TARGET: 40
        }
        coverage = self.params.get(xc.COVERAGE)
        if coverage == 40:
            coverage_thresholds[rc.TUMOUR_MIN] = 40
            coverage_thresholds[rc.TUMOUR_TARGET] = 50
        elif coverage == 80:
            coverage_thresholds[rc.TUMOUR_MIN] = 80
            coverage_thresholds[rc.TUMOUR_TARGET] = 100
        else:
            raise RuntimeError("Unknown depth of coverage")
        return coverage_thresholds

    def build_fda_approved_info(self):
        return self.build_therapy_info(self.FDA_APPROVED)

    def build_gene_url(self, gene):
        return '/'.join([self.ONCOKB_URL_BASE, gene])

    def build_genomic_biomarkers(self,input_dir,sample_ID):
        rows = []
        genomic_biomarkers_path = os.path.join(input_dir, self.GENOMIC_BIOMARKERS)
        with open(genomic_biomarkers_path, 'w') as genomic_biomarkers_file:
            #print .maf header
            print("HUGO_SYMBOL\tSAMPLE_ID\tALTERATION", file=genomic_biomarkers_file)
            rows.append(self.call_TMB(sample_ID,genomic_biomarkers_file))
            rows.append(self.call_MSI(sample_ID,genomic_biomarkers_file))
        out_path = oncokb_annotator(
            self.clinical_data[dc.TUMOUR_SAMPLE_ID],
            self.params.get(xc.ONCOTREE_CODE).upper(),
            input_dir,
            input_dir,
            self.params.get(xc.ONCOKB_CACHE),
            self.log_level,
            self.log_path
        ).annotate_maf(genomic_biomarkers_path)
        data = {
            rc.CLINICALLY_RELEVANT_VARIANTS: len(rows),
            rc.BODY: rows
        }
        return data

    def build_genomic_landscape_info(self):
        # need to calculate TMB and percentiles
        cohort = self.read_cohort()
        data = {}
        data[rc.TMB_TOTAL] = self.tmb_count
        # TODO See GCGI-347 for possible updates to V7_TARGET_SIZE
        data[rc.TMB_PER_MB] = round(self.tmb_count/self.V7_TARGET_SIZE, 2)
        data[rc.PERCENT_GENOME_ALTERED] = int(round(self.read_fga()*100, 0))
        csp = self.read_cancer_specific_percentile(data[rc.TMB_PER_MB], cohort, self.closest_tcga_lc)
        data[rc.CANCER_SPECIFIC_PERCENTILE] = csp
        data[rc.CANCER_SPECIFIC_COHORT] = cohort
        pcp = self.read_pan_cancer_percentile(data[rc.TMB_PER_MB])
        data[rc.PAN_CANCER_PERCENTILE] = int(round(pcp, 0))
        data[rc.PAN_CANCER_COHORT] = self.PAN_CANCER_COHORT
        return data

    def build_investigational_therapy_info(self):
        return self.build_therapy_info(self.INVESTIGATIONAL)

    def build_patient_info(self):
        # TODO import clinical data column names from Djerba constants
        data = {}
        tumour_id = self.clinical_data[dc.TUMOUR_SAMPLE_ID]
        data[rc.ASSAY_NAME] = self.build_assay_name()
        data[rc.BLOOD_SAMPLE_ID] = self.clinical_data[dc.BLOOD_SAMPLE_ID]
        data[rc.SEX] = self.clinical_data[dc.SEX]
        data[rc.PATIENT_LIMS_ID] = self.clinical_data[dc.PATIENT_LIMS_ID]
        data[rc.PATIENT_STUDY_ID] = self.clinical_data[dc.PATIENT_STUDY_ID]
        data[rc.PRIMARY_CANCER] = self.clinical_data[dc.CANCER_TYPE_DESCRIPTION]
        data[rc.REPORT_ID] = "{0}-v{1}".format(tumour_id, self.clinical_data[dc.REPORT_VERSION])
        data[rc.REQ_ID] = self.config[ini.INPUTS][ini.REQ_ID]
        data[rc.REQ_APPROVED_DATE] = self.clinical_data[dc.REQ_APPROVED_DATE]
        data[rc.SITE_OF_BIOPSY_OR_SURGERY] = self.clinical_data[dc.SAMPLE_ANATOMICAL_SITE]
        data[rc.STUDY] = self.config[ini.INPUTS][ini.STUDY_ID]
        data[rc.PROJECT] = self.params.get(xc.PROJECT)
        data[rc.TUMOUR_SAMPLE_ID] = tumour_id
        return data
    
    def build_versions(self):
        data = {}
        data[rc.PICARD_VERSION] = self.config[ini.VERSIONS][ini.PICARD_VERSION]
        data[rc.PICARD_LINK] = self.config[ini.VERSIONS][ini.PICARD_LINK]
        data[rc.REFERENCE_GENOME_VERSION] = self.config[ini.VERSIONS][ini.REFERENCE_GENOME_VERSION]
        data[rc.REFERENCE_GENOME_LINK] = self.config[ini.VERSIONS][ini.REFERENCE_GENOME_LINK]       
        data[rc.BWAMEM_VERSION] = self.config[ini.VERSIONS][ini.BWAMEM_VERSION]
        data[rc.BWAMEM_LINK] = self.config[ini.VERSIONS][ini.BWAMEM_LINK]
        data[rc.GATK_VERSION] = self.config[ini.VERSIONS][ini.GATK_VERSION]
        data[rc.GATK_LINK] = self.config[ini.VERSIONS][ini.GATK_LINK]
        data[rc.MUTECT2_VERSION] = self.config[ini.VERSIONS][ini.MUTECT2_VERSION]
        data[rc.MUTECT2_LINK] = self.config[ini.VERSIONS][ini.MUTECT2_LINK]
        data[rc.VARIANTEFFECTPREDICTOR_VERSION] = self.config[ini.VERSIONS][ini.VARIANTEFFECTPREDICTOR_VERSION]
        data[rc.VARIANTEFFECTPREDICTOR_LINK] = self.config[ini.VERSIONS][ini.VARIANTEFFECTPREDICTOR_LINK]       
        data[rc.MANE_VERSION] = self.config[ini.VERSIONS][ini.MANE_VERSION]
        data[rc.MANE_LINK] = self.config[ini.VERSIONS][ini.MANE_LINK]       
        data[rc.SEQUENZA_VERSION] = self.config[ini.VERSIONS][ini.SEQUENZA_VERSION]
        data[rc.SEQUENZA_LINK] = self.config[ini.VERSIONS][ini.SEQUENZA_LINK]     
        data[rc.MICROSATELLITE_VERSION] = self.config[ini.VERSIONS][ini.MICROSATELLITE_VERSION]
        data[rc.MICROSATELLITE_LINK] = self.config[ini.VERSIONS][ini.MICROSATELLITE_LINK]
        data[rc.STAR_VERSION] = self.config[ini.VERSIONS][ini.STAR_VERSION]
        data[rc.STAR_LINK] = self.config[ini.VERSIONS][ini.STAR_LINK]        
        data[rc.RSEM_VERSION] = self.config[ini.VERSIONS][ini.RSEM_VERSION]
        data[rc.RSEM_LINK] = self.config[ini.VERSIONS][ini.RSEM_LINK]        
        data[rc.STARFUSION_VERSION] = self.config[ini.VERSIONS][ini.STARFUSION_VERSION]
        data[rc.STARFUSION_LINK] = self.config[ini.VERSIONS][ini.STARFUSION_LINK]        
        data[rc.ARRIBA_VERSION] = self.config[ini.VERSIONS][ini.ARRIBA_VERSION]
        data[rc.ARRIBA_LINK] = self.config[ini.VERSIONS][ini.ARRIBA_LINK]        
        data[rc.MAVIS_VERSION] = self.config[ini.VERSIONS][ini.MAVIS_VERSION]
        data[rc.MAVIS_LINK] = self.config[ini.VERSIONS][ini.MAVIS_LINK]        
        return data
     
    def build_sample_info(self):
        data = {}
        data[rc.CALLABILITY_PERCENT] = float(self.clinical_data[dc.PCT_V7_ABOVE_80X])
        data[rc.COVERAGE_MEAN] = float(self.clinical_data[dc.MEAN_COVERAGE])
        data[rc.PLOIDY] = float(self.clinical_data[dc.SEQUENZA_PLOIDY])
        data[rc.PURITY_PERCENT] = round(float(self.clinical_data[dc.SEQUENZA_PURITY_FRACTION])*100, 1)
        data[rc.ONCOTREE_CODE] = self.params.get(xc.ONCOTREE_CODE).upper()
        data[rc.SAMPLE_TYPE] = self.clinical_data[dc.SAMPLE_TYPE]
        return data

    def build_small_mutations_and_indels(self):
        # read in small mutations; output rows for oncogenic mutations
        self.logger.debug("Building data for small mutations and indels table")
        rows = []
        mutation_copy_states = self.read_mutation_copy_states()
        mutation_LOH_states = self.read_mutation_LOH()
        if self.is_wgts:
            mutation_expression = self.read_expression()
        else:
            mutation_expression = {}
        with open(os.path.join(self.input_dir, self.MUTATIONS_EXTENDED_ONCOGENIC)) as data_file:
            for input_row in csv.DictReader(data_file, delimiter="\t"):
                gene = input_row[self.HUGO_SYMBOL_TITLE_CASE]
                cytoband = self.get_cytoband(gene)
                protein = input_row[self.HGVSP_SHORT]
                row = {
                    rc.GENE: gene,
                    rc.GENE_URL: self.build_gene_url(gene),
                    rc.CHROMOSOME: cytoband,
                    rc.PROTEIN: protein,
                    rc.PROTEIN_URL: self.build_alteration_url(gene, protein, self.oncotree_uc),
                    rc.MUTATION_TYPE: re.sub('_', ' ', input_row[self.VARIANT_CLASSIFICATION]),
                    rc.EXPRESSION_METRIC: mutation_expression.get(gene), # None for WGS assay
                    rc.VAF_PERCENT: int(round(float(input_row[self.TUMOUR_VAF]), 2)*100),
                    rc.TUMOUR_DEPTH: int(input_row[rc.TUMOUR_DEPTH]),
                    rc.TUMOUR_ALT_COUNT: int(input_row[rc.TUMOUR_ALT_COUNT]),
                    rc.COPY_STATE: mutation_copy_states.get(gene, self.UNKNOWN),
                    rc.LOH_STATE: mutation_LOH_states[gene],
                    rc.ONCOKB: self.parse_oncokb_level(input_row)
                }
                rows.append(row)
        self.logger.debug("Sorting and filtering small mutation and indel rows")
        rows = list(filter(self.oncokb_filter, self.sort_variant_rows(rows)))
        for row in rows: self.all_reported_variants.add((row.get(rc.GENE), row.get(rc.CHROMOSOME)))
        data = {
            rc.HAS_EXPRESSION_DATA: self.is_wgts,
            rc.CLINICALLY_RELEVANT_VARIANTS: len(rows),
            rc.TOTAL_VARIANTS: self.total_somatic_mutations,
            rc.BODY: rows
        }
        return data

    def build_svs_and_fusions(self):
        # table has 2 rows for each oncogenic fusion
        self.logger.debug("Building data for structural variants and fusions table")
        rows = []
        for fusion in self.gene_pair_fusions:
            oncokb_level = fusion.get_oncokb_level()
            for gene in fusion.get_genes():
                cytoband = self.get_cytoband(gene)
                row =  {
                    rc.GENE: gene,
                    rc.GENE_URL: self.build_gene_url(gene),
                    rc.CHROMOSOME: cytoband,
                    rc.FRAME: fusion.get_frame(),
                    rc.FUSION: fusion.get_fusion_id_new(),
                    rc.MUTATION_EFFECT: fusion.get_mutation_effect(),
                    rc.ONCOKB: oncokb_level
                }
                rows.append(row)
        rows = list(filter(self.oncokb_filter, rows)) # sorting is done by fusion reader
        for row in rows: self.all_reported_variants.add((row.get(rc.GENE), row.get(rc.CHROMOSOME)))
        distinct_oncogenic_genes = len(set([row.get(rc.GENE) for row in rows]))
        data = {
            rc.CLINICALLY_RELEVANT_VARIANTS: distinct_oncogenic_genes,
            rc.TOTAL_VARIANTS: self.total_fusion_genes,
            rc.BODY: rows
        }
        return data

    def build_supplementary_info(self):
        rows = []
        if self.failed:
            self.logger.debug("Failed report, omitting construction of supplementary gene information table")
        else:
            self.logger.debug("Building data for supplementary gene information table")
            variants = sorted(list(self.all_reported_variants))
            gene_summaries = self.read_oncokb_gene_summaries()
            for [gene, cytoband] in variants:
                row = {
                    rc.GENE: gene,
                    rc.GENE_URL: self.build_gene_url(gene),
                    rc.CHROMOSOME: cytoband,
                    rc.SUMMARY: gene_summaries.get(gene, 'OncoKB summary not available')
                }
                rows.append(row)
        self.logger.debug("Found {0} supplementary info rows".format(len(rows)))
        return rows

    def build_therapy_info(self, level):
        # build the "FDA approved" and "investigational" therapies data
        # defined respectively as OncoKB levels 1/2/R1 and R2/3A/3B/4
        # OncoKB "LEVEL" columns contain treatment if there is one, 'NA' otherwise
        # Output columns:
        # - the gene name, with oncoKB link (or pair of names/links, for fusions)
        # - Alteration name, eg. HGVSp_Short value, with oncoKB link
        # - Treatment
        # - OncoKB level
        self.logger.debug("Building therapy info for level: {0}".format(level))
        if level == self.FDA_APPROVED:
            levels = oncokb.FDA_APPROVED_LEVELS
        elif level == self.INVESTIGATIONAL:
            levels = oncokb.INVESTIGATIONAL_LEVELS
        else:
            raise RuntimeError("Unknown therapy level: '{0}'".format(level))
        rows = []
        with open(os.path.join(self.input_dir, self.MUTATIONS_EXTENDED_ONCOGENIC)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                gene = row[self.HUGO_SYMBOL_TITLE_CASE]
                alteration = row[self.HGVSP_SHORT]
                [max_level, therapies] = self.parse_max_oncokb_level_and_therapies(row, levels)
                if max_level:
                    rows.append(self.treatment_row(gene, alteration, max_level, therapies))
        with open(os.path.join(self.input_dir, self.CNA_ANNOTATED)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                gene = row[self.HUGO_SYMBOL_UPPER_CASE]
                alteration = row[self.ALTERATION_UPPER_CASE]
                [max_level, therapies] = self.parse_max_oncokb_level_and_therapies(row, levels)
                if max_level:
                    rows.append(self.treatment_row(gene, alteration, max_level, therapies))
        if self.gene_pair_fusions: # omit for WGS-only reports
            for fusion in self.gene_pair_fusions:
                genes = fusion.get_genes()
                alteration = rc.FUSION
                if level == self.FDA_APPROVED:
                    max_level = fusion.get_fda_level()
                    therapies = fusion.get_fda_therapies()
                else:
                    max_level = fusion.get_inv_level()
                    therapies = fusion.get_inv_therapies()
                if max_level:
                    rows.append(self.treatment_row(genes, alteration, max_level, therapies))

        if os.path.exists(os.path.join(self.input_dir, self.BIOMARKERS_ANNOTATED)):
            with open(os.path.join(self.input_dir, self.BIOMARKERS_ANNOTATED)) as data_file:
                for row in csv.DictReader(data_file, delimiter="\t"):
                    gene = 'Biomarker'
                    alteration = row[self.ALTERATION_UPPER_CASE]
                    [max_level, therapies] = self.parse_max_oncokb_level_and_therapies(row, levels)
                    if max_level:
                        rows.append(self.treatment_row(gene, alteration, max_level, therapies))
        else:
            msg = "No other biomarkers file at \"{0}\", skipping other biomarkers".format(os.path.join(self.input_dir, self.BIOMARKERS_ANNOTATED))
            self.logger.debug(msg)
        rows = list(filter(self.oncokb_filter, self.sort_therapy_rows(rows)))
        return rows

    def call_MSI(self,sample_ID,genomic_biomarkers_file):
        #convert MSI number into Low, inconclusive or High call
        msi = self.extract_msi()
        if msi >= self.MSI_CUTOFF:
            metric_call = "MSI-H"
            metric_text = "Microsatellite Instability High (MSI-H)"
            print("Other Biomarkers\t"+sample_ID+"\tMSI-H", file=genomic_biomarkers_file)
        elif msi < self.MSI_CUTOFF and msi >= self.MSS_CUTOFF:
            metric_call = "INCONCLUSIVE"
            metric_text = "Inconclusive Microsatellite Instability status"
        elif msi < self.MSS_CUTOFF:
            metric_call = "MSS"
            metric_text = "Microsatellite Stable (MSS)"
        else:
            msg = "MSI not a number"
            self.logger.error(msg)
            raise RuntimeError(msg)
        msi_plot_location = self.write_biomarker_plot(self.input_dir,"msi")
        msi_plot_base64 = converter().convert_svg(msi_plot_location, 'MSI plot')
        row = {
            rc.ALT: rc.MSI,
            rc.METRIC_VALUE: msi,
            rc.METRIC_CALL: metric_call,
            rc.METRIC_TEXT: metric_text,
            rc.ALT_URL: "https://www.oncokb.org/gene/Other%20Biomarkers/MSI-H",
            rc.METRIC_PLOT: msi_plot_base64
        }
        return(row)

    def call_TMB(self,sample_ID,genomic_biomarkers_file):
        #convert TMB number into Low or High call
        tmb = self.build_genomic_landscape_info()[rc.TMB_PER_MB]
        tmb_plot_placeholder = "see tmb_plot"
        if tmb >= 10:
            metric_call = "TMB-H"
            metric_text = "Tumour Mutational Burden High (TMB-H, &#8805 10 coding mutations / Mb)"
            print("Other Biomarkers\t"+sample_ID+"\tTMB-H", file=genomic_biomarkers_file)
        elif tmb < 10:
            metric_call = "TMB-L"
            metric_text = "Tumour Mutational Burden Low (TMB-L, < 10 coding mutations / Mb)"
        else:
            msg = "TMB not a number"
            self.logger.error(msg)
            raise RuntimeError(msg)
        row = {
            rc.ALT: rc.TMB,
            rc.METRIC_VALUE: tmb,
            rc.METRIC_CALL: metric_call,
            rc.METRIC_TEXT: metric_text,
            rc.ALT_URL: "https://www.oncokb.org/gene/Other%20Biomarkers/TMB-H",
            rc.METRIC_PLOT: tmb_plot_placeholder
        }
        return(row)

    def cytoband_sort_order(self, cb_input):
        """Cytobands are (usually) of the form [integer][p or q][decimal]; also deal with edge cases"""
        end = (999, 'z', 999999)
        if cb_input in self.UNCLASSIFIED_CYTOBANDS:
            msg = "Cytoband \"{0}\" is unclassified, moving to end of sort order".format(cb_input)
            self.logger.debug(msg)
            (chromosome, arm, band) = end
        else:
            try:
                cb = re.split('\s+', cb_input).pop(0) # remove suffixes like 'alternate reference locus'
                cb = re.split('-', cb).pop(0) # take the first part of eg. 2q22.2-q22.3
                chromosome = re.split('[pq]', cb).pop(0)
                if chromosome == 'X':
                    chromosome = 23
                elif chromosome == 'Y':
                    chromosome = 24
                else:
                    chromosome = int(chromosome)
                arm = 'a' # arm may be missing; default to beginning of sort order
                band = 0 # band may be missing; default to beginning of sort order
                if re.match('^([0-9]+|[XY])[pq]', cb):
                    arm = re.split('[^pq]+', cb).pop(1)
                if re.match('^([0-9]+|[XY])[pq][0-9]+\.*\d*$', cb):
                    band = float(re.split('[^0-9\.]+', cb).pop(1))
            except (IndexError, ValueError) as err:
                # if error occurs in ordering, move to end of sort order
                msg = "Cannot parse cytoband \"{0}\" for sorting; ".format(cb_input)+\
                      "moving to end of sort order. No further action is needed. "+\
                      "Reason for parsing failure: {0}".format(err)
                self.logger.warning(msg)
                (chromosome, arm, band) = end
        return (chromosome, arm, band)

    def extract_msi(self):
        MSI = 0.0
        with open(os.path.join(self.input_dir, self.MSI_FILE), 'r') as msi_file:
            reader_file = csv.reader(msi_file, delimiter="\t")
            for row in reader_file:
                try: 
                    MSI = float(row[2])
                except IndexError as err:
                    msg = "Incorrect number of columns in msisensor row: '{0}'".format(row)+\
                          "read from '{0}'".format(os.path.join(self.input_dir, self.MSI_FILE))
                    self.logger.error(msg)
                    raise RuntimeError(msg) from err
        return MSI

    def get_cytoband(self, gene_name):
        cytoband = self.cytoband_map.get(gene_name)
        if not cytoband:
            cytoband = 'Unknown'
            msg = "Cytoband for gene '{0}' not found in {1}".format(gene_name, self.cytoband_path)
            self.logger.info(msg)
        return cytoband

    def read_cancer_specific_percentile(self, tmb, cohort, cancer_type):
        # Read percentile for given TMB/Mb and cohort
        # We use statsmodels to compute the ECDF
        # See: https://stackoverflow.com/a/15792672
        # Introduces dependency on Pandas, but still the most convenient solution
        if cohort == self.NA:
            percentile = self.NA
        else:
            if cohort == self.COMPASS:
                data_filename = self.TMBCOMP_EXTERNAL
            else:
                data_filename = self.TMBCOMP_TCGA
            tmb_array = []
            with open(os.path.join(self.data_dir, data_filename)) as data_file:
                for row in csv.DictReader(data_file, delimiter="\t"):
                    if row[self.CANCER_TYPE_HEADER] == cancer_type:
                        tmb_array.append(float(row[self.TMB_HEADER]))
            ecdf = ECDF(tmb_array)
            percentile = int(round(ecdf(tmb)*100, 0)) # return an integer percentile
        return percentile

    def read_cohort(self):
        # cohort is:
        # 1) COMPASS if 'closest TCGA' is paad
        # 2) CANCER.TYPE from tmbcomp-tcga.txt if one matches 'closest TCGA'
        # 3) NA otherwise
        #
        # Note: cohort in case (1) is really the Source column in tmbcomp-externaldata.txt
        # but for now this only has one value
        # TODO need to define a procedure for adding more data cohorts
        tcga_cancer_types = set()
        with open(os.path.join(self.data_dir, self.TMBCOMP_TCGA)) as tcga_file:
            reader = csv.reader(tcga_file, delimiter="\t")
            for row in reader:
                tcga_cancer_types.add(row[3])
        if self.closest_tcga_lc == 'paad':
            cohort = self.COMPASS
        elif self.closest_tcga_lc in tcga_cancer_types:
            cohort = self.closest_tcga_lc
        else:
            cohort = self.NA
        return cohort

    def read_clinical_data(self):
        input_path = os.path.join(self.input_dir, dc.CLINICAL_DATA_FILENAME)
        with open(input_path) as input_file:
            reader = csv.reader(input_file, delimiter="\t")
            header = next(reader)
            body = next(reader)
        if len(header)!=len(body):
            raise ValueError("Clinical data header and body of unequal length")
        clinical_data = {}
        for i in range(len(header)):
            clinical_data[header[i]] = body[i]
        return clinical_data

    def read_cnv_data(self):
        input_path = os.path.join(self.input_dir, self.CNA_ANNOTATED)
        variants = []
        with open(input_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                total += 1
                gene = row[self.HUGO_SYMBOL_UPPER_CASE]
                cytoband = self.get_cytoband(gene)
                variant = {
                    rc.GENE: gene,
                    rc.GENE_URL: self.build_gene_url(gene),
                    rc.ALT: row[self.ALTERATION_UPPER_CASE],
                    rc.CHROMOSOME: cytoband,
                    rc.ONCOKB: self.parse_oncokb_level(row)
                }
                variants.append(variant)
        return variants

    def read_cytoband_map(self):
        input_path = self.cytoband_path
        cytobands = {}
        with open(input_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                cytobands[row[self.HUGO_SYMBOL_TITLE_CASE]] = row['Chromosome']
        return cytobands

    def read_expression(self):
        # read the expression metric (may be zscore or percentage, depending on choice of input file)
        input_path = os.path.join(self.input_dir, self.expr_input)
        expr = {}
        with open(input_path) as input_file:
            for row in csv.reader(input_file, delimiter="\t"):
                if row[0]=='Hugo_Symbol':
                    continue
                gene = row[0]
                try:
                    metric = float(row[1])
                except ValueError as err:
                    msg = 'Cannot convert expression value "{0}" to float, '.format(row[1])+\
                          '; using 0 as fallback value: {0}'.format(err)
                    self.logger.warning(msg)
                    metric = 0.0
                expr[gene] = metric
        return expr

    def read_fga(self):
        input_path = os.path.join(self.input_dir, self.DATA_SEGMENTS)
        total = 0
        with open(input_path) as input_file:
            for row in csv.DictReader(input_file, delimiter="\t"):
                if abs(float(row['seg.mean'])) >= self.MINIMUM_MAGNITUDE_SEG_MEAN:
                    total += int(row['loc.end']) - int(row['loc.start'])
        # TODO see GCGI-347 for possible updates to genome size
        fga = float(total)/self.GENOME_SIZE
        return fga

    def read_genomic_summary(self):
        with open(os.path.join(self.input_dir, dc.GENOMIC_SUMMARY_FILENAME)) as in_file:
            return in_file.read().strip()
    
    def read_technical_notes(self):
        with open(os.path.join(self.input_dir, dc.TECHNICAL_NOTES_FILENAME)) as in_file:
            return in_file.read().strip()

    def read_mutation_copy_states(self):
        # convert copy state to human readable string; return mapping of gene -> copy state
        copy_state_conversion = {
            0: "Neutral",
            1: "Gain",
            2: "Amplification",
            -1: "Shallow Deletion",
            -2: "Deep Deletion"
        }
        copy_states = {}
        with open(os.path.join(self.input_dir, self.CNA_SIMPLE)) as in_file:
            first = True
            for row in csv.reader(in_file, delimiter="\t"):
                if first:
                    first = False
                else:
                    [gene, category] = [row[0], int(row[1])]
                    copy_states[gene] = copy_state_conversion.get(category, self.UNKNOWN)
        return copy_states

    def read_mutation_LOH(self):
        # convert A-allele ratio to LOH; return mapping of gene -> LOH
        loh_states = {}
        with open(os.path.join(self.input_dir, self.CNA_ARATIO)) as in_file:
            first = True
            for row in csv.reader(in_file, delimiter="\t"):
                if first:
                    first = False
                else:
                    [gene, aratio] = [row[0], float(row[1])]
                    if(aratio == 0.0):
                        lohcall = "Yes"
                    else:
                        lohcall = "No"   
                    loh_states[gene] = (lohcall+' ('+str(round(aratio,1))+')')
        return loh_states

    def read_oncokb_gene_summaries(self):
        summaries = {}
        with open(os.path.join(self.data_dir, self.ALL_CURATED_GENES)) as in_file:
            for row in csv.DictReader(in_file, delimiter="\t"):
                summaries[row['hugoSymbol']] = row['summary']
        return summaries

    def read_pan_cancer_percentile(self, tmb):
        tmb_array = []
        with open(os.path.join(self.data_dir, self.TMBCOMP_TCGA)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                tmb_array.append(float(row[self.TMB_HEADER]))
        ecdf = ECDF(tmb_array)
        percentile = ecdf(tmb)*100
        return percentile

    def read_somatic_mutation_totals(self):
        # Count the somatic mutations
        # Splice_Region is *excluded* for TMB, *included* in our mutation tables and counts
        # Splice_Region mutations are of interest to us, but excluded from the standard TMB definition
        # The TMB mutation count is (independently) implemented and used in vaf_plot.R
        # See JIRA ticket GCGI-496
        total = 0
        excluded = 0
        with open(os.path.join(self.input_dir, self.MUTATIONS_EXTENDED)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                total += 1
                if row.get(self.VARIANT_CLASSIFICATION) in self.TMB_EXCLUDED:
                    excluded += 1
        tmb_count = total - excluded
        msg = "Found {} small mutations and indels, of which {} are counted for TMB".format(total,
                                                                                            tmb_count)
        self.logger.debug(msg)
        return [total, tmb_count]

    def run(self):
        """Main method to generate JSON from a report directory"""
        # for now, this writes plots to the input report directory and returns paths in JSON
        # if needed, could write plots to a tempdir and return base64 blobs in JSON
        self.logger.info("Building clinical report data")
        data = {}
        if self.failed:
            self.logger.info("Building JSON for report with FAILED QC")
        else:
            self.logger.info("Building JSON for report with PASSED QC")
        data[rc.ASSAY_TYPE] = self.params.get(xc.ASSAY_TYPE)
        data[rc.AUTHOR] = self.params.get(xc.AUTHOR)
        data[rc.OICR_LOGO] = os.path.join(self.html_dir, 'OICR_Logo_RGB_ENGLISH.png')
        data[rc.PATIENT_INFO] = self.build_patient_info()
        data[rc.SAMPLE_INFO] = self.build_sample_info()
        data[rc.GENOMIC_SUMMARY] = self.read_genomic_summary()
        data[rc.TECHNICAL_NOTES] = self.read_technical_notes()
        data[rc.COVERAGE_THRESHOLDS] = self.build_coverage_thresholds()
        data[rc.FAILED] = self.failed
        data[rc.PURITY_FAILURE] = self.params.get(xc.PURITY_FAILURE)
        data[rc.REPORT_DATE] = None
        data[rc.DJERBA_VERSION] = __version__
        data[rc.PIPELINE_VERSION] = self.config[ini.SETTINGS][ini.PIPELINE_VERSION]
        data[rc.VERSIONS]  = self.build_versions() 

        if not self.failed:
            # additional data for non-failed reports
            data[rc.GENOMIC_BIOMARKERS] = self.build_genomic_biomarkers(self.input_dir,self.clinical_data[dc.TUMOUR_SAMPLE_ID])
            data[rc.APPROVED_BIOMARKERS] = self.build_fda_approved_info()
            data[rc.INVESTIGATIONAL_THERAPIES] = self.build_investigational_therapy_info()
            data[rc.GENOMIC_LANDSCAPE_INFO] = self.build_genomic_landscape_info()
            tmb = data[rc.GENOMIC_LANDSCAPE_INFO][rc.TMB_PER_MB]
            pga = data[rc.GENOMIC_LANDSCAPE_INFO][rc.PERCENT_GENOME_ALTERED]
            data[rc.TMB_PLOT] = self.write_tmb_plot(tmb, self.input_dir)
            data[rc.VAF_PLOT] = self.write_vaf_plot(self.input_dir)
            data[rc.CNV_PLOT] = converter().convert_svg(self.write_cnv_plot(self.input_dir), 'CNV plot')
            data[rc.PGA_PLOT] = converter().convert_svg(self.write_pga_plot(pga, self.input_dir), 'PGA plot')
            data[rc.SMALL_MUTATIONS_AND_INDELS] = self.build_small_mutations_and_indels()
            data[rc.TOP_ONCOGENIC_SOMATIC_CNVS] = self.build_copy_number_variation()
            if self.params.get(xc.ASSAY_TYPE) == rc.ASSAY_WGTS:
                data[rc.STRUCTURAL_VARIANTS_AND_FUSIONS] = self.build_svs_and_fusions()
            else:
                data[rc.STRUCTURAL_VARIANTS_AND_FUSIONS] = None
        # build supplementary gene info last; refers back to variants discovered (if any)
        data[rc.SUPPLEMENTARY_GENE_INFO] = self.build_supplementary_info()
        self.logger.info("Finished building clinical report data for JSON output")
        return data

    def sort_therapy_rows(self, rows):
        # sort FDA/investigational therapy rows
        # extract a gene name from 'genes and urls' dictionary keys
        rows = sorted(
            rows,
            key=lambda row: sorted(list(row.get(rc.GENES_AND_URLS).keys())).pop(0)
        )
        rows = sorted(rows, key=lambda row: self.oncokb_sort_order(row[rc.ONCOKB]))
        return rows

    def sort_variant_rows(self, rows):
        # sort rows oncokb level, then by cytoband, then by gene name
        self.logger.debug("Sorting rows by gene name")
        rows = sorted(rows, key=lambda row: row[rc.GENE])
        self.logger.debug("Sorting rows by cytoband")
        rows = sorted(rows, key=lambda row: self.cytoband_sort_order(row[rc.CHROMOSOME]))
        self.logger.debug("Sorting rows by oncokb level")
        rows = sorted(rows, key=lambda row: self.oncokb_sort_order(row[rc.ONCOKB]))
        return rows

    def treatment_row(self, genes_arg, alteration, max_level, therapies):
        # genes argument may be a string, or an iterable of strings
        core_biomarker_url = "https://www.oncokb.org/gene/Other%20Biomarkers"
        if isinstance(genes_arg, str):
            genes_and_urls = {genes_arg: self.build_gene_url(genes_arg)}
        else:
            genes_and_urls = {gene: self.build_gene_url(gene) for gene in genes_arg}
        if alteration == rc.FUSION:
            alt_url = self.build_alteration_url('-'.join(genes_arg), alteration, self.oncotree_uc)
        elif alteration == "TMB-H" or alteration == "MSI-H":
            genes_and_urls = {
                "Biomarker": core_biomarker_url
            }
            if alteration == "TMB-H":
                alt_url = '/'.join([core_biomarker_url,"TMB-H/"])
            if alteration == "MSI-H":
                alt_url = '/'.join([core_biomarker_url,"Microsatellite%20Instability-High/"])
        else:
            alt_url = self.build_alteration_url(genes_arg, alteration, self.oncotree_uc)
        row = {
            rc.GENES_AND_URLS: genes_and_urls,
            rc.ALT: alteration,
            rc.ALT_URL: alt_url,
            rc.ONCOKB: max_level,
            rc.TREATMENT: therapies
        }
        return row

    def write_biomarker_plot(self, out_dir,marker):
        out_path = os.path.join(out_dir, marker+'.svg')
        args = [
            os.path.join(self.r_script_dir, 'biomarkers_plot.R'),
            '-d', self.input_dir
        ]
        subprocess_runner(self.log_level, self.log_path).run(args)
        self.logger.info("Wrote biomarkers plot to {0}".format(out_path))
        return out_path

    def write_cnv_plot(self, out_dir):
            out_path = os.path.join(out_dir, 'seg_CNV_plot.svg')
            args = [
                os.path.join(self.r_script_dir, 'cnv_plot.R'),
                '--segfile',  os.path.join(self.input_dir, 'aratio_segments.txt'),
                '--segfiletype', 'sequenza',
                '-d',out_dir
            ]
            subprocess_runner(self.log_level, self.log_path).run(args)
            self.logger.info("Wrote CNV plot to {0}".format(out_path))
            return out_path

    def write_pga_plot(self, pga, out_dir):
        out_path = os.path.join(out_dir, 'pga.svg')
        args = [
            os.path.join(self.r_script_dir, 'pga_plot.R'),
            '-o', out_path,
            '-p', str(pga)
        ]
        subprocess_runner(self.log_level, self.log_path).run(args)
        self.logger.info("Wrote PGA plot to {0}".format(out_path))
        return out_path

    def write_tmb_plot(self, tmb, out_dir):
        out_path = os.path.join(out_dir, 'tmb.svg')
        args = [
            os.path.join(self.r_script_dir, 'tmb_plot.R'),
            '-c', self.closest_tcga_lc,
            '-o', out_path,
            '-t', str(tmb)
        ]
        subprocess_runner(self.log_level, self.log_path).run(args)
        self.logger.info("Wrote TMB plot to {0}".format(out_path))
        return out_path

    def write_vaf_plot(self, out_dir):
        out_path = os.path.join(out_dir, 'vaf.svg')
        args = [
            os.path.join(self.r_script_dir, 'vaf_plot.R'),
            '-d', self.input_dir,
            '-o', out_path
        ]
        subprocess_runner(self.log_level, self.log_path).run(args)
        self.logger.info("Wrote VAF plot to {0}".format(out_path))
        return out_path
    

class fusion_reader(composer_base):

    # read files from an input directory and gather information on fusions
    DATA_FUSIONS_NEW = 'data_fusions_new_delimiter.txt'
    DATA_FUSIONS_OLD = 'data_fusions.txt'
    DATA_FUSIONS_ANNOTATED = 'data_fusions_oncokb_annotated.txt'
    FUSION_INDEX = 4
    HUGO_SYMBOL = 'Hugo_Symbol'

    def __init__(self, input_dir, log_level=logging.WARNING, log_path=None):
        super().__init__(log_level, log_path) # calls the parent constructor; creates logger
        self.input_dir = input_dir
        self.old_to_new_delimiter = self.read_fusion_delimiter_map()
        fusion_data = self.read_fusion_data()
        annotations = self.read_annotation_data()
        # delly results have been removed from fusion data; do the same for annotations
        for key in [k for k in annotations.keys() if k not in fusion_data]:
            del annotations[key]
        # now check the key sets match
        if set(fusion_data.keys()) != set(annotations.keys()):
            msg = "Distinct fusion identifiers and annotations do not match. "+\
                  "Fusion data: {0}; ".format(sorted(list(set(fusion_data.keys()))))+\
                  "Annotations: {0}".format(sorted(list(set(annotations.keys()))))
            self.logger.error(msg)
            raise RuntimeError(msg)
        [fusions, self.total_fusion_genes] = self._collate_row_data(fusion_data, annotations)
        # sort the fusions by oncokb level & fusion ID
        fusions = sorted(fusions, key=lambda f: f.get_fusion_id_new())
        self.fusions = sorted(fusions, key=lambda f: self.oncokb_sort_order(f.get_oncokb_level()))

    def _collate_row_data(self, fusion_data, annotations):
        fusions = []
        fusion_genes = set()
        self.logger.debug("Starting to collate fusion table data.")
        intragenic = 0
        for fusion_id in fusion_data.keys():
            if len(fusion_data[fusion_id])==1:
                # add intragenic fusions to the gene count, then skip
                fusion_genes.add(fusion_data[fusion_id][0][self.HUGO_SYMBOL])
                intragenic += 1
                continue
            elif len(fusion_data[fusion_id]) >= 3:
                msg = "More than 2 fusions with the same name: {0}".format(fusion_id)
                self.logger.error(msg)
                raise RuntimeError(msg)
            gene1 = fusion_data[fusion_id][0][self.HUGO_SYMBOL]
            gene2 = fusion_data[fusion_id][1][self.HUGO_SYMBOL]
            fusion_genes.add(gene1)
            fusion_genes.add(gene2)
            frame = fusion_data[fusion_id][0]['Frame']
            ann = annotations[fusion_id]
            effect = ann['MUTATION_EFFECT']
            oncokb_level = self.parse_oncokb_level(ann)
            fda = self.parse_max_oncokb_level_and_therapies(ann, oncokb.FDA_APPROVED_LEVELS)
            [fda_level, fda_therapies] = fda
            inv = self.parse_max_oncokb_level_and_therapies(ann, oncokb.INVESTIGATIONAL_LEVELS)
            [inv_level, inv_therapies] = inv
            fusions.append(
                fusion(
                    fusion_id,
                    self.old_to_new_delimiter[fusion_id],
                    gene1,
                    gene2,
                    frame,
                    effect,
                    oncokb_level,
                    fda_level,
                    fda_therapies,
                    inv_level,
                    inv_therapies
                )
            )
        total = len(fusions)
        total_fusion_genes = len(fusion_genes)
        msg = "Finished collating fusion table data. "+\
              "Found {0} fusion rows for {1} distinct genes; ".format(total, total_fusion_genes)+\
              "excluded {0} intragenic rows.".format(intragenic)
        self.logger.info(msg)
        return [fusions, total_fusion_genes]

    def get_fusions(self):
        return self.fusions

    def get_total_fusion_genes(self):
        return self.total_fusion_genes

    def read_annotation_data(self):
        # annotation file has exactly 1 line per fusion
        annotations_by_fusion = {}
        with open(os.path.join(self.input_dir, self.DATA_FUSIONS_ANNOTATED)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                annotations_by_fusion[row['Fusion']] = row
        return annotations_by_fusion

    def read_fusion_data(self):
        # data file has 1 or 2 lines per fusion (1 if it has an intragenic component, 2 otherwise)
        data_by_fusion = {}
        with open(os.path.join(self.input_dir, self.DATA_FUSIONS_OLD)) as data_file:
            delly_count = 0
            total = 0
            for row in csv.DictReader(data_file, delimiter="\t"):
                total += 1
                if row['Method']=='delly':
                    # omit delly structural variants (which are not fusions, and not yet validated)
                    delly_count += 1
                else:
                    # make fusion ID consistent with format in annotated file
                    fusion_id = re.sub('None', 'intragenic', row['Fusion'])
                    if fusion_id in data_by_fusion:
                        data_by_fusion[fusion_id].append(row)
                    else:
                        data_by_fusion[fusion_id] = [row,]
        self.logger.debug("Read {0} rows of fusion input; excluded {1} delly rows".format(total, delly_count))
        return data_by_fusion

    def read_fusion_delimiter_map(self):
        # read the mapping of fusion identifiers from old - to new :: delimiter
        # ugly workaround implemented in upstream R script; TODO refactor to something neater
        with open(os.path.join(self.input_dir, self.DATA_FUSIONS_OLD)) as file_old:
            old = [row[self.FUSION_INDEX] for row in csv.reader(file_old, delimiter="\t")]
        with open(os.path.join(self.input_dir, self.DATA_FUSIONS_NEW)) as file_new:
            new = [row[self.FUSION_INDEX] for row in csv.reader(file_new, delimiter="\t")]
        if len(old) != len(new):
            msg = "Fusion ID lists from {0} are of unequal length".format(report_dir)
            self.logger.error(msg)
            raise RuntimeError(msg)
        # first item of each list is the header, which can be ignored
        return {old[i]:new[i] for i in range(1, len(old))}

class fusion:
    # container for data relevant to reporting a fusion

    def __init__(
            self,
            fusion_id_old,
            fusion_id_new,
            gene1,
            gene2,
            frame,
            effect,
            oncokb_level,
            fda_level,
            fda_therapies,
            inv_level,
            inv_therapies
    ):
        self.fusion_id_old = fusion_id_old
        self.fusion_id_new = fusion_id_new
        self.gene1 = gene1
        self.gene2 = gene2
        self.frame = frame
        self.effect = effect
        self.oncokb_level = oncokb_level
        self.fda_level = fda_level
        self.fda_therapies = fda_therapies
        self.inv_level = inv_level
        self.inv_therapies = inv_therapies

    def get_fusion_id_old(self):
        return self.fusion_id_old

    def get_fusion_id_new(self):
        return self.fusion_id_new

    def get_genes(self):
        return [self.gene1, self.gene2]

    def get_frame(self):
        return self.frame

    def get_mutation_effect(self):
        return self.effect

    def get_oncokb_level(self):
        return self.oncokb_level

    def get_fda_level(self):
        return self.fda_level

    def get_fda_therapies(self):
        return self.fda_therapies

    def get_inv_level(self):
        return self.inv_level

    def get_inv_therapies(self):
        return self.inv_therapies

