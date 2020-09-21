#!/home/afortuna/anaconda3/bin/python3

# This script will calculate TMB given a MAF File
import pandas as pd
from statsmodels.distributions.empirical_distribution import ECDF
import sys

#tcga_path = "/home/afortuna/Desktop/CAP/genomicLandscapeTest/tcga_tmbs.txt"
#cancer_type = "gbm"
#tmb = 5


def find_pct(tcga_path, cancer_type, tmb):
    tmb = int(tmb)
    tcga = pd.read_csv(tcga_path, sep='\t', header=0, names=['sample', 'TMB', 'callable', 'cancerType'])
    cohorttmbs = tcga.loc[tcga["cancerType"] == cancer_type]
    tcgaPct = ECDF(tcga.TMB)(tmb)
    cohortPct = ECDF(cohorttmbs.TMB)(tmb)
    print(tcgaPct)
    print(cohortPct)


find_tmb(sys.argv[1], sys.argv[2], sys.argv[3])
