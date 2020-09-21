#! /usr/bin/env python3

# This script will calculate TMB given a MAF File
import pandas as pd
import sys

def find_fga(seg_path, sampleName):
    seg = pd.read_csv(seg_path, sep='\t', skiprows= 0)
    seg_sample = seg.loc[(seg["ID"] == sampleName)]
    seg_alt = seg_sample.loc[(seg_sample["seg.mean"] > 0.2) | (seg_sample["seg.mean"] < -0.2)]
    denom = sum(seg_sample['loc.end'] - seg_sample['loc.start'])
    fga = sum(seg_alt['loc.end'] - seg_alt['loc.start'])/denom
    return fga

if __name__ == "__main__":
    print(find_fga(sys.argv[1], sys.argv[2]))
