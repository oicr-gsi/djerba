#!/home/afortuna/anaconda3/bin/python3

# This script will calculate TMB given a MAF File
import pandas as pd
import numpy as np
from statsmodels.distributions.empirical_distribution import ECDF
import sys


maf_path = "/home/afortuna/Desktop/CAP/genomicLandscapeTest/OCT_010118_Ut_P_WG_OCT_010118_TS.somatic.somatic.maf.txt.gz"
bed_path = "/home/afortuna/Desktop/CAP/genomicLandscapeTest/S31285117_Regions.bed"
tcga_path = "/home/afortuna/Desktop/CAP/genomicLandscapeTest/tcga_tmbs.txt"
cancer_type = "gbm"
call = 90

def find_tmb(maf_path, bed_path, callable):
    percent = int(callable)
    bed = pd.read_csv(bed_path, sep='\t', skiprows=2, header=None, names=['chrom', 'start', 'end'])
    tcga =pd.read_csv(tcga_path, sep='\t', names=['sample', 'tmb', 'callable', 'cancerType'])
    targetSpace = (percent / 100) * sum(bed['end'] - bed['start']) / 1000000
    keep = ['Missense_Mutation', 'Frame_Shift_Del', 'In_Frame_Del', 'Frame_Shift_Ins',
            'In_Frame_Ins', 'Splice_Site', 'Translation_Start_Site', 'Nonsense_Mutation', 'Nonstop_Mutation']
    pmaf = pd.read_csv(maf_path, sep='\t', skiprows=1)
    tmb = round(len(pmaf.loc[pmaf["Variant_Classification"].isin(keep)]) / targetSpace, 2)
    print(tmb)

find_tmb(sys.argv[1], sys.argv[2], sys.argv[3])
