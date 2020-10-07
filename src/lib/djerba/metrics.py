"""Classes to contain genetic_alteration metric functions; see prototypes directory"""

import json
import pandas as pd
from statsmodels.distributions.empirical_distribution import ECDF
import sys

class mutation_extended_metrics:

    """Metrics for the MUTATION_EXTENDED alteration type"""
    
    def __init__(self, maf_path, bed_path, tcga_path, cancer_type):
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
