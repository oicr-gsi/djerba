"""Classes to contain genetic_alteration metric functions; see prototypes directory"""

import gzip
import json
import logging
import pandas as pd
import re

from statsmodels.distributions.empirical_distribution import ECDF
from math import isnan
from djerba.utilities.base import base

class mutation_extended_gene_metrics(base):

    """
    Gene-level fields for the MUTATION_EXTENDED alteration type

    Includes fields for Elba output:
    - Allele Fraction Percentage
    - Chromosome
    - Gene
    - FDA Approved Treatment
    - OncoKB
    - Protein Change
    - Variant Reads And Total Reads
    """

    # MAF column headers
    HUGO_SYMBOL = 'Hugo_Symbol'
    CHROMOSOME = 'Chromosome'
    HGVSP_SHORT = 'HGVSp_Short'
    T_DEPTH = 't_depth'
    T_ALT_COUNT = 't_alt_count'
    HIGHEST_LEVEL = 'Highest_level'
    FDA_APPROVED_TREATMENT = 'FDA_Approved_Treatment'
    LEVEL_1  = 'LEVEL_1'
    LEVEL_2A = 'LEVEL_2A'
    LEVEL_2B = 'LEVEL_2B'
    LEVEL_3A = 'LEVEL_3A'
    LEVEL_3B = 'LEVEL_3B'
    LEVEL_4  = 'LEVEL_4'
    LEVEL_R1 = 'LEVEL_R1'
    LEVEL_R2 = 'LEVEL_R2'
    REQUIRED_MAF_COLS = [
        HUGO_SYMBOL,
        CHROMOSOME,
        HGVSP_SHORT,
        T_DEPTH,
        T_ALT_COUNT,
    ]
    BIOMARKER_LEVELS = [
        LEVEL_1,
        LEVEL_2A,
        LEVEL_2B,
        LEVEL_3A,
        LEVEL_3B,
        LEVEL_4,
        LEVEL_R1,
        LEVEL_R2
    ]

    # Output headers
    PROTEIN_CHANGE = 'Protein_Change'
    ALLELE_FRACTION_PERCENTILE = 'Allele_Fraction_Percentile'
    VARIANT_READS_AND_TOTAL_READS = 'Variant_Reads_And_Total_Reads'
    ONCOKB = 'OncoKB'

    def __init__(self, maf_path, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        cols = self._find_columns_to_use(maf_path)
        df = pd.read_csv(maf_path, usecols=cols, delimiter="\t", comment="#")
        if df.size == 0:
            msg = "No rows found in MAF input %s" % maf_path
            self.logger.error(msg)
            raise RuntimeError(msg)
        else:
            self.logger.debug("Found %d MAF rows from input path %s" % (df.size, maf_path))
        self.metrics = {}
        for index, row in df.iterrows():
            total = row[self.T_DEPTH]
            variants = row[self.T_ALT_COUNT]
            try:
                afp = (float(variants)/float(total))*100
            except ZeroDivisionError:
                afp = "NA"
            oncokb = row.get(self.HIGHEST_LEVEL)
            if oncokb == None:
                oncokb = "NA"
            self.metrics[row[self.HUGO_SYMBOL]] = {
                self.CHROMOSOME: row[self.CHROMOSOME],
                self.PROTEIN_CHANGE: row[self.HGVSP_SHORT],
                self.VARIANT_READS_AND_TOTAL_READS: "%d/%d" % (variants, total),
                self.ALLELE_FRACTION_PERCENTILE: afp,
                self.ONCOKB: oncokb,
                self.FDA_APPROVED_TREATMENT: self._find_treatment_string(row)
            }
            self.logger.debug("Found metrics for gene %s" % row[self.HUGO_SYMBOL])

    def _find_columns_to_use(self, maf_path):
        """
        Read column headers from the MAF file, to determine what columns to input in pandas
        Handles the case where not all OncoKB LEVEL columns are present
        MAF files may have 100+ columns, so this is preferred to reading in the whole file
        """
        if re.search("\.gz$", maf_path):
            in_file = gzip.open(maf_path, 'rt')
        else:
            in_file = open(maf_path, 'r')
        header_line = None
        # read the first non-comment line to get column headers
        while True:
            line = in_file.readline()
            if line == '': # end of file
                break
            elif re.match("#", line):
                continue
            else:
                header_line = line
                break
        in_file.close()
        if not header_line:
            msg = "No header line found in MAF file '%s'" % maf_path
            self.logger.error(msg)
            raise RuntimeError(msg)
        column_names = re.split("\t", line.strip())
        self.logger.debug("Found MAF column names: "+", ".join(column_names))
        missing = []
        for name in self.REQUIRED_MAF_COLS:
            if not name in column_names:
                missing.append(name)
        if len(missing) > 0:
            msg = "Missing required MAF columns: "+", ".join(missing)
            self.logger.error(msg)
            raise RuntimeError(msg)
        use_cols = self.REQUIRED_MAF_COLS.copy() # list of columns to read
        optional_total = 0
        optional_cols = [self.HIGHEST_LEVEL]
        optional_cols.extend(self.BIOMARKER_LEVELS)
        for name in optional_cols:
            if name in column_names:
                use_cols.append(name)
                optional_total += 1
        if optional_total == 0:
            msg = "No optional MAF columns found. OncoKB annotation not applied? "+\
                  "OncoKB output fields will receive 'NA' values."
            self.logger.warning(msg)
        self.logger.debug("Found MAF columns for input: "+", ".join(use_cols))
        return use_cols

    def _find_treatment_string(self, row):
        """
        Find the 'FDA Approved Treatment' string
        Concatenation of level codes and approved treatments
        """
        # This string is a temporary placeholder, will be replaced by a more complex structure
        # See https://jira.oicr.on.ca/browse/GCGI-69
        biomarker_values = []
        for level in self.BIOMARKER_LEVELS:
            value = row.get(level) # will be None if no column in MAF file for this level
            # test for null values (unfortunately there is no standard representation for these)
            if value != '' and value != 'NA' and value != None and str(value) != 'nan':
                biomarker_values.append('%s:%s' % (level, value))
        if len(biomarker_values) == 0:
            return 'NA'
        else:
            return ';'.join(biomarker_values)

    def get_metrics_for_gene(self, gene):
        """Get metric dictionary for the named gene, or None if gene is not present"""
        return self.metrics.get(gene)

    def get_metrics(self):
        return self.metrics

class mutation_extended_sample_metrics(base):

    """
    Sample-level metrics for the MUTATION_EXTENDED alteration type

    Includes metrics for Elba output:
    - TMB_PER_MB
    """
    
    def __init__(self, maf_path, bed_path, tcga_path, cancer_type, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.tmb = self._find_tmb(maf_path, bed_path)        
        [self.tcga_tmb, self.tcga_cohort_tmb] = self._read_tcga(tcga_path, cancer_type)
        self.tcga_pct = ECDF(self.tcga_tmb)(self.tmb)
        self.cohort_pct = ECDF(self.tcga_cohort_tmb)(self.tmb)
        
    def _find_tmb(self, maf_path, bed_path):
        """Find the TMB metric: tumor mutation burden / megabase"""
        names = ['chrom', 'start', 'end']
        maf = pd.read_csv(maf_path, sep='\t', skiprows=1)
        bed = pd.read_csv(bed_path, sep='\t', skiprows=2, header=None, names=names)
        target_space = sum(bed['end'] - bed['start']) / 1000000
        keep = [
            'Missense_Mutation',
            'Frame_Shift_Del',
            'In_Frame_Del',
            'Frame_Shift_Ins',
            'In_Frame_Ins',
            'Splice_Site',
            'Translation_Start_Site',
            'Nonsense_Mutation',
            'Nonstop_Mutation'
        ]
        tmb = len(maf.loc[maf["Variant_Classification"].isin(keep)]) / target_space
        return tmb

    def _read_tcga(self, tcga_path, cancer_type):
        """Read the TCGA path and return a pair of dictionaries for TMB"""
        tcga_cols = ['sample', 'tcgaTMB', 'callable', 'cancerType']
        tcga = pd.read_csv(tcga_path, sep='\t', header=0, names=tcga_cols)
        tcga_tmb =  tcga.tcgaTMB
        tcga_cohort = tcga.loc[tcga["cancerType"] == cancer_type]
        tcga_cohort = tcga_cohort.rename(columns={'tcgaTMB': 'cohortTMB'})
        tcga_cohort_tmb = tcga_cohort.cohortTMB
        return (tcga_tmb, tcga_cohort_tmb)

    def get_cosmic_sigs(self):
        """
        TODO: Compute the COSMIC_SIGS metric
        - Currently implemented as an R script
        - Not yet ready for production, requires more validation
        - Return "NA" as a placeholder for now
        """
        return "NA"

    def get_tmb(self):
        return self.tmb

    def get_tcga_pct(self):
        return self.tcga_pct
    
    def get_cohort_pct(self):
        return self.cohort_pct
    
    def get_tcga_tmb_as_dict(self):
        """Convert the pandas Series to a dictionary"""
        return self.tcga_tmb.to_dict()

    def get_cohort_tmb_as_dict(self):
        """Convert the pandas Series to a dictionary"""
        return self.tcga_cohort_tmb.to_dict()
