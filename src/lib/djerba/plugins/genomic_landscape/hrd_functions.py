"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import re
import logging
import json

from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner

NCCN_HRD_RECOMMENDED_TYPES = ['Ovarian Cancer']

def annotate_hrd(hrd_result, oncotree_code, data_dir):
    if hrd_result == 'HRD':
        oncotree_main = pull_main_type_from_oncotree(oncotree_code, data_dir)
        if oncotree_main in NCCN_HRD_RECOMMENDED_TYPES:
            oncokb_level = '2'
            annotation_tier = "Approved"
        else:
            oncokb_level = '3B'
            annotation_tier = "Investigational"
        treatment_options = {
            "Tier": annotation_tier,
            "OncoKB level": oncokb_level,
            "Treatments": "PARP inhibitors",
            "Gene": "HRD",
            "Gene_URL": "",
            "Alteration": "HRD",
            "Alteration_URL": "https://www.nccn.org/professionals/physician_gls/pdf/ovarian_blocks.pdf"
        }
    else:
        treatment_options = None
    return(treatment_options)

def find_tree_values(id, json_repr):
    results = []
    id = id.upper()
    def _decode_dict(a_dict):
        try:
            results.append(a_dict[id])
        except KeyError:
            pass
        return a_dict
    json.loads(json_repr, object_hook=_decode_dict) 
    return results

def pull_main_type_from_oncotree(this_oncotree_code, data_dir):
    ONCOTREE_FILE = '20231214-OncoTree.json'
    tree_file = os.path.join(data_dir, ONCOTREE_FILE) 

    f = open(tree_file, 'r')
    tree_data = f.read()
    f.close()

    tree_info_on_this_code = find_tree_values(this_oncotree_code, tree_data)

    for code in tree_info_on_this_code:
        mainType = code['mainType']
    return(mainType)

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
        HRD_long = "Homologous Recombination Deficiency (HRD)"
        HRD_short = "HRD"
        actionable = True
    else:
        HRD_long = "Homologous Recombination Proficiency"
        HRD_short = "HR Proficient"
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

