"""Djerba plugin for pwgs reporting"""
import csv
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import djerba.plugins.genomic_landscape.constants as glc

from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
from djerba.util.validator import path_validator

class hrd_processor(logger):

    def __init__(self, log_level, log_path):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)

    ONCOTREE_FILE = 'OncoTree.json'
    NCCN_ANNOTATION_FILENAME = 'NCCN_annotations.txt'
    HRD_CUTOFF = 0.7
    ONCOTREE_INDEX = 3
    URL_INDEX = 4

    def annotate_NCCN(self, hrd_result, oncotree_code, oncotree_dir, nccn_dir):
        """
        Use NCCN Annotation file to filter by oncotree code and add NCCN URL
        """
        treatment_options = None
        if hrd_result == 'HRD':
            
            # Catch unknown oncotree code. 
            try:
                oncotree_main = self.read_oncotree_main_type(oncotree_code, oncotree_dir)
            except IndexError:
                 msg = "Could not find oncotree code {0} in OncoTree.json. Skipping treatment options for HRD.".format(oncotree_code)
                 self.logger.warning(msg)
                 return treatment_options 
            
            # Otherwise, proceed with known oncotree code.
            nccn_annotation_path = os.path.join(nccn_dir, self.NCCN_ANNOTATION_FILENAME)
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

    def make_HRD_plot(self, work_dir, hrd_score):
        """
        Takes the HRD probability score as input.
        This will plot a red dot.
        Potentially to-do: add BRCA1/BRCA2 probability scores?
        Writes the graph to a png; does not return anything.
        """

        # Get output name
        output = os.path.join(work_dir, glc.HRD_PLOT_FILENAME)

        # Set up plot aesthetics
        fig, ax = plt.subplots(figsize=(4, 1.1))
        ax.set_xlabel("Probability of HRD", fontsize=7, color='black', labelpad=1)

        x_ticks = [hrd_score, 0.25, 0.50, 0.75, 1.00]
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks(x_ticks)
        ax.xaxis.set_minor_locator(plt.NullLocator())
        ax.set_xticklabels([f"{v:.2f}" for v in x_ticks], fontsize=6)
        ax.get_yaxis().set_visible(False)

        # Plot red dot
        ax.plot(hrd_score, 0.5, marker='o', markersize=9.5, color='red', markeredgewidth=0.5, markerfacecolor='none', clip_on=False)
        ax.plot(hrd_score, 0.5, marker='o', markersize=2.2, color='red', clip_on=False)
        ax.text(hrd_score, 0.3, "This Sample", color='red', fontsize=5.5, ha='center', va='top', clip_on=False)

        # Plot basics: threshold, HR-P and HR-D labels
        ax.axvline(x=0.50, color='grey', linestyle='--', linewidth=0.8)
        ax.text(0.25, 0.85, 'HR-P', color='gray', fontsize=6, ha='center')
        ax.text(0.75, 0.85, 'HR-D', color='gray', fontsize=6, ha='center')

        # Get rid of borders (matches old Rscript plot look)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        plt.tight_layout()
        plt.savefig(output, format="png", dpi=300, bbox_inches='tight', backend='Cairo')

    def read_oncotree_main_type(self, oncotree_code, data_dir):
        """
        Read Oncotree JSON file and return main type for given code
        """
        with open(os.path.join(data_dir, self.ONCOTREE_FILE)) as tree_file:
            json_as_text = tree_file.read()
        mainType = self.find_main_value_from_tree(oncotree_code, json_as_text)
        return(mainType)

    def get_hrd_results(self, hrd_path):
        """
        Takes in CHORD results
        Outputs the HRD probability score and the status as defined by CHORD
        """

        df = pd.read_csv(hrd_path, sep = '\t')
        hrd_score = float(df["p_hrd"].iloc[0])
        hrd_status = df["hr_status"].iloc[0]
        hrd_remarks = str(df["remarks_hr_status"].iloc[0])

        return hrd_score, hrd_status, hrd_remarks

    def convert_hrd_plot(self, work_dir):
        """
        Read VAF plot from file if it exists and return as a base64 string
        Else, return False
        """
        image_converter = converter(self.log_level, self.log_path)
        plot_path = os.path.join(work_dir, glc.HRD_PLOT_FILENAME)
        if os.path.exists(os.path.join(work_dir, glc.HRD_PLOT_FILENAME)):
            hrd_plot = image_converter.convert_png(plot_path, 'HRD plot')
        else:
            hrd_plot = None
        return hrd_plot

    def convert_hrd_remarks(self, hrd_remarks):
        """
        HRD remarks for the undetermined HRD case are given as:
        
        CHORD requires >=100 indels to accurately determine whether a sample is HRD. If this criterion is not met, hr_status will be cannot_be_determined and remarks_hr_status will be "<50 indels".
    
        CHORD cannot be applied to MSI samples. If an MSI sample is detected, hr_status will be cannot_be_determined and remarks_hr_status will be "Has MSI (>14000 indel.rep)"
    
        CHORD requires >=30 SVs to accurately determine HRD subtype. If this criterion is not met, hrd_type will be cannot_be_determined, and remarks_hr_status will be "<30 SVs."

        So this function will take the text given and convert it to text that's appropriate to display.

        """

        dictionary = {"<50 indels": "sample has <50 indels", \
                      "Has MSI (>14000 indel.rep)": "sample has MSI", \
                      "<30 SVs": "sample has <30 SVs"}

        # Default to "Unknown" as a reason if it's something else:
        conversion = dictionary.get(hrd_remarks, "Unknown")
        return conversion

    def run(self, work_dir, hrd_path):
        """
        Main HRD function, makes biomarker according to biomarker schema
        TODO: make official schema for biomarkers (with schema checks)
        """
        hrd_score, hrd_status, hrd_remarks = self.get_hrd_results(hrd_path)

        if hrd_status in [glc.HR_DEFICIENT, glc.HR_PROFICIENT]:
            if hrd_status == glc.HR_DEFICIENT:
                HRD_long = "Homologous Recombination Deficiency (HRD)"
                HRD_short = "HRD"
                actionable = True
            elif hrd_status == glc.HR_PROFICIENT:
                HRD_long = "Homologous Recombination Proficiency"
                HRD_short = "HR Proficient"
                actionable = False
            self.make_HRD_plot(work_dir, hrd_score)
            hrd_base64 = self.convert_hrd_plot(work_dir)
        else:
            HRD_long = self.convert_hrd_remarks(hrd_remarks)
            HRD_short = "Undetermined"
            actionable = False
            hrd_base64 = "Not Applicable"

        results =  {
                'Alteration': 'HRD',
                'Alteration_URL': '',
                'Genomic alteration actionable': actionable,
                'Genomic biomarker alteration': HRD_short,
                'Genomic biomarker plot': hrd_base64,
                'Genomic biomarker text': HRD_long,
                'Genomic biomarker value': hrd_score,
            }
        return results

