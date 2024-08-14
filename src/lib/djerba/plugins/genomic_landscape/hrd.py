"""Djerba plugin for pwgs reporting"""
import csv
import json
import os

from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.validator import path_validator

class hrd_processor(logger):

    def __init__(self, log_level, log_path):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, log_path)
        self.validator = path_validator(log_level, log_path)

    ONCOTREE_FILE = 'OncoTree.json'
    NCCN_ANNOTATION_FILENAME = 'NCCN_annotations.txt'
    HRD_CUTOFF = 0.7
    ONCOTREE_INDEX = 3
    URL_INDEX = 4

    def annotate_NCCN(self, hrd_result, oncotree_code, data_dir):
        """
        Use NCCN Annotation file to filter by oncotree code and add NCCN URL
        """
        treatment_options = None
        if hrd_result == 'HRD':
            oncotree_main = self.read_oncotree_main_type(oncotree_code, data_dir)
            nccn_annotation_path = os.path.join(data_dir, self.NCCN_ANNOTATION_FILENAME)
            self.validator.validate_input_file(nccn_annotation_path)
            with open(nccn_annotation_path) as NCCN_annotation_file:
                tsv_reader = csv.reader(NCCN_annotation_file, delimiter="\t")
                for marker_row in tsv_reader:
                    if oncotree_main in marker_row[self.ONCOTREE_INDEX]:
                        oncokb_level = 'P'
                        annotation_tier = "Prognostic"
                        treatment_options = {
                            "Tier": annotation_tier,
                            "OncoKB level": oncokb_level,
                            "Treatments": "",
                            "Gene": "HRD",
                            "Gene_URL": "",
                            "Alteration": "Genomic Landscape",
                            "Alteration_URL": marker_row[self.URL_INDEX]
                        }
        return treatment_options

    def find_main_value_from_tree(self, oncotree_code, json_as_text):
        """
        Look in JSON and return sub-dictionaries that contain that oncotree_code
        There may be a simpler way to do this (without the object_hook), but this works for now
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
        mainType = tree_info_on_this_code.pop()['mainType']
        return mainType

    def make_HRD_plot(self, output_dir):
        args = [
            os.path.join(os.path.dirname(__file__),'Rscripts/hrd_plot.R'),
            '--dir', output_dir,
            '--cutoff', str(self.HRD_CUTOFF)
        ]
        pwgs_results = subprocess_runner(self.log_level, self.log_path).run(args)
        return pwgs_results.stdout.split('"')[1]

    def read_oncotree_main_type(self, oncotree_code, data_dir):
        """
        Read Oncotree JSON file and return main type for given code
        """
        with open(os.path.join(data_dir, self.ONCOTREE_FILE)) as tree_file:
            json_as_text = tree_file.read()
        mainType = self.find_main_value_from_tree(oncotree_code, json_as_text)
        return(mainType)

    def run(self, work_dir, hrd_path):
        """
        Main HRD function, makes biomarker according to biomarker schema
        TODO: make official schema for biomarkers (with schema checks)
        """
        hrd_data = self.write_hrd_quartiles(work_dir, hrd_path)
        hrd_base64 = self.make_HRD_plot(work_dir)
        if hrd_data["hrdetect_call"]["Probability.w"][1] > self.HRD_CUTOFF:
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

    def write_hrd_quartiles(self, work_dir, hrd_path):
        """
        Reads JSON from hrDetect and writes quartiles file for R plotting
        """
        self.validator.validate_output_dir(work_dir)
        self.validator.validate_input_file(hrd_path)
        with open(hrd_path) as f:
            hrd_data = json.load(f)
        out_path = os.path.join(work_dir, 'hrd.tmp.txt')
        with open(out_path, 'w') as out_file:
            for row in hrd_data["hrdetect_call"]:
                quartiles = hrd_data["hrdetect_call"][row]
                print("\t".join((row,"\t".join([str(item) for item in list(quartiles)]))), file=out_file)
        return hrd_data


