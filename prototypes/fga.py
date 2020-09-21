#!/home/afortuna/anaconda3/bin/python3

# This script will calculate TMB given a MAF File
import pandas as pd
import sys

seg_path = "/home/afortuna/Desktop/CAP/genomicLandscapeTest/data_segments.txt"
sampleName = "COM-00278-CAP"

def find_fga(seg_path, sampleName):
    seg = pd.read_csv(seg_path, sep='\t', skiprows= 0)
    seg_sample = seg.loc[(seg["ID"] == sampleName)]
    seg_alt = seg_sample.loc[(seg_sample["seg.mean"] > 0.2) | (seg_sample["seg.mean"] < -0.2)]
    denom = sum(seg_sample['loc.end'] - seg_sample['loc.start'])
    fga = round(sum(seg_alt['loc.end'] - seg_alt['loc.start'])/denom,2)
    print(fga)

find_fga(sys.argv[1], sys.argv[2])