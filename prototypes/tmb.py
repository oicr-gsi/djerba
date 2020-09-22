#! /usr/bin/env python3

# This script will calculate TMB given a MAF File, and TMB percentile
import pandas as pd
from statsmodels.distributions.empirical_distribution import ECDF
import sys


def find_tmb(maf_path, bed_path, tcga_path, cancer_type):
    maf = pd.read_csv(maf_path, sep='\t', skiprows=1)
    bed = pd.read_csv(bed_path, sep='\t', skiprows=2, header=None, names=['chrom', 'start', 'end'])
    target_space = sum(bed['end'] - bed['start']) / 1000000
    tcga = pd.read_csv(tcga_path, sep='\t', header=0, names=['sample', 'TMB', 'callable', 'cancerType'])
    tcga_cohort = tcga.loc[tcga["cancerType"] == cancer_type]
    keep = ['Missense_Mutation', 'Frame_Shift_Del', 'In_Frame_Del', 'Frame_Shift_Ins',
            'In_Frame_Ins', 'Splice_Site', 'Translation_Start_Site', 'Nonsense_Mutation', 'Nonstop_Mutation']
    tmb = len(maf.loc[maf["Variant_Classification"].isin(keep)]) / target_space
    tcga_cohort = tcga.loc[tcga["cancerType"] == cancer_type]
    tcga_pct = ECDF(tcga.TMB)(tmb)
    cohort_pct = ECDF(tcga_cohort.TMB)(tmb)
    tcga_tmb = [tcga.TMB]
    tcga_cohort_tmb = [tcga_cohort.TMB]
    return tmb, tcga_pct, cohort_pct, tcga_tmb, tcga_cohort_tmb

if __name__ == "__main__":
    print(find_tmb(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
