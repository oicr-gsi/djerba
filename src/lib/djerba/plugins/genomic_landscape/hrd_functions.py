"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import re
import logging
import json

from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner

def run(work_dir, hrd_path):
    hrd_file = open(hrd_path)
    hrd_data = json.load(hrd_file)
    hrd_file.close()
    out_path = os.path.join(work_dir, 'hrd.tmp.txt')
    try:
        os.remove(out_path)
    except OSError:
        pass
    for row in hrd_data["hrdetect_call"]:
        write_hrd(out_path, row, hrd_data["hrdetect_call"][row])
    hrd_base64 = write_plot(work_dir)       
    if hrd_data["hrdetect_call"]["Probability.w"][1] > 0.7:
        HRD_long = "Homologous Recombination Deficiency (HR-D)"
        HRD_short = "HR-D"
        actionable = True
    else:
        HRD_long = "Homologous Recombination Proficiency (HR-P)"
        HRD_short = "HR-P"
        actionable = False
    results =  {
            'Alteration': 'HRD',
            'Alteration_URL': '',
            'Genomic alteration actionable': actionable,
            'Genomic biomarker alteration': HRD_short,
            'Genomic biomarker plot': hrd_base64,
            'Genomic biomarker text': HRD_long,
            'Genomic biomarker value': hrd_data["hrdetect_call"]["Probability.w"][1],
            'QC' : hrd_data["QC"],
            
        }
    return results

def write_hrd(out_path, row, quartiles):
    with open(out_path, 'a') as out_file:
        print("\t".join((row,"\t".join([str(item) for item in list(quartiles)]))), file=out_file)
    return out_path

def write_plot(output_dir ):
    args = [
        os.path.join(os.path.dirname(__file__),'Rscripts/hrd_plot.R'),
        '--dir', output_dir
    ]
    pwgs_results = subprocess_runner().run(args)
    return(pwgs_results.stdout.split('"')[1])