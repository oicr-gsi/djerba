"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import re
import logging
import json

from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner

ONCOTREE_FILE = 'OncoTree.json'
NCCN_ANNOTATION_FILE = 'NCCN_annotations.txt'
HRD_CUTOFF = "0.7"
ONCOTREE_INDEX = 3
URL_INDEX = 4

def annotate_NCCN(hrd_result, oncotree_code, data_dir):
    """
    Use NCCN Annotation file to filter by oncotree code and add NCCN URL
    """
    treatment_options = None
    if hrd_result == 'HRD':
        oncotree_main = pull_main_type_from_oncotree(oncotree_code, data_dir)
        NCCN_annotation_path = os.path.join(data_dir, NCCN_ANNOTATION_FILE)
        with open(NCCN_annotation_path) as NCCN_annotation_file:
            tsv_reader = csv.reader(NCCN_annotation_file, delimiter="\t")
            for marker_row in tsv_reader:
                if oncotree_main in marker_row[ONCOTREE_INDEX]:
                    oncokb_level = 'P'
                    annotation_tier = "Prognostic"
                    treatment_options = {
                        "Tier": annotation_tier,
                        "OncoKB level": oncokb_level,
                        "Treatments": "",
                        "Gene": "HRD",
                        "Gene_URL": "",
                        "Alteration": "Genomic Landscape",
                        "Alteration_URL": marker_row[URL_INDEX]
                    }        
    return(treatment_options)

def find_main_value_from_tree(oncotree_code, json_as_text):
    """
    Look in JSON and return sub-dictionaries that contain that oncotree_code
    """
    tree_info_on_this_code = []
    oncotree_code = oncotree_code.upper()
    def _decode_dict(a_dict):
        try:
            tree_info_on_this_code.append(a_dict[oncotree_code])
        except KeyError:
            pass
        return a_dict
    json.loads(json_as_text, object_hook=_decode_dict) 
    for code in tree_info_on_this_code:
        mainType = code['mainType']
    return mainType

def make_HRD_plot(output_dir ):
    args = [
        os.path.join(os.path.dirname(__file__),'Rscripts/hrd_plot.R'),
        '--dir', output_dir,
        '--cutoff', HRD_CUTOFF
    ]
    pwgs_results = subprocess_runner().run(args)
    return(pwgs_results.stdout.split('"')[1])

def pull_main_type_from_oncotree(this_oncotree_code, data_dir):
    """
    Read Oncotree JSON file and return main type for given code
    """
    tree_path = os.path.join(data_dir, ONCOTREE_FILE)
    with open(tree_path) as tree_file:
        json_as_text = tree_file.read()
    mainType = find_main_value_from_tree(this_oncotree_code, json_as_text)
    return(mainType)

def run(work_dir, hrd_path):
    """
    Main HRD function, makes biomarker according to biomarker schema
    TODO: make official schema for biomarkers (with schema checks)
    """
    hrd_data = write_hrd_quartiles(work_dir, hrd_path)
    hrd_base64 = make_HRD_plot(work_dir)       
    if hrd_data["hrdetect_call"]["Probability.w"][1] > float(HRD_CUTOFF):
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

def write_hrd_quartiles(work_dir, hrd_path):
    """
    Reads JSON from hrDetect and writes quartiles file for R plotting
    """
    with open(hrd_path) as f:
        hrd_data = json.load(f)
    out_path = os.path.join(work_dir, 'hrd.tmp.txt')
    with open(out_path, 'w') as out_file:
        for row in hrd_data["hrdetect_call"]:
            quartiles = hrd_data["hrdetect_call"][row]
            print("\t".join((row,"\t".join([str(item) for item in list(quartiles)]))), file=out_file)
    return hrd_data


