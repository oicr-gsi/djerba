"""Djerba plugin for pwgs reporting"""
import csv
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd


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

    def make_HRD_plot(self, output_dir):
        """
        Create plot for HRD probability. 
        """
        boot = pd.read_csv(os.path.join(output_dir, 'hrd.tmp.txt'), sep = "\t", header=None, names = ["var", "q1", "median_value", "q3"])
        boot["Sample"] = "Sample"
        weights_df = boot[boot["var"].isin(["del.mh.prop.w", "SNV3.w", "SV3.w", "SV5.w", "hrd.w"])].copy()

        #equation [4] in Davies et al. 2017
        intercept = boot.loc[boot["var"] == "intercept.w", "median_value"].iloc[0]
        weights_df["probability"] = 1 / (1 + np.exp(-(intercept + weights_df["median_value"])))

        #rename variables
        var_map = {
                "SV5.w": "Large Deletions",
                "SV3.w": "Tandem Duplications",
                "SNV3.w": "COSMIC SBS3",
                "hrd.w": "LOH",
                "del.mh.prop.w": "Microhomologous Deletions"                    
                }
        weights_df["var_long"] = weights_df["var"].map(var_map)
        weights_df["var_longer"] = (weights_df["var_long"] + ": " + weights_df["probability"].round(2).map(lambda x: f"{x:.2f}"))
        weights_df = weights_df.sort_values("var_long", ascending=False)

        #adjust position of "This sample" label to score
        adjust_label_w_position = 0.25
        probability_value = boot.loc[boot["var"] == "Probability.w", "median_value"].iloc[0]
        if probability_value > 0.5:
            adjust_label_w_position = 0.5

        out_path = os.path.join(output_dir, "hrd.svg")
        fig, ax = plt.subplots(figsize=(8, 1.6))
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")

        bottom = 0
        for _, row in weights_df.iterrows():
            ax.barh(
                y="Sample",
                width=row["probability"],
                left=bottom,
                height=0.5,
                color="#FFFFFF",
                edgecolor="#FFFFFF",
                label=row["var_longer"]
                                                                                
                    )
            bottom += row["probability"]

        ax.hlines(y = weights_df["Sample"],
                xmin = boot.loc[boot["var"] == "Probability.w", "q1"].iloc[0], 
                xmax = boot.loc[boot["var"] == "Probability.w", "q3"].iloc[0],
                colors = "#FF0000")

        ax.axvline(self.HRD_CUTOFF, color="lightgray")
        ax.text(self.HRD_CUTOFF / 2, 0.3, "HR-P", color="#4d4d4d", ha="center", fontsize=14)
        ax.text(0.85, 0.3, "HR-D", color="#4d4d4d", ha="center", fontsize=14)
        
        ax.scatter(probability_value, "Sample", s=200, facecolors="none", edgecolors="#FF0000")
        ax.scatter(probability_value, "Sample", s=30, color="#FF0000")

        ax.text(
            probability_value,
            "Sample",
            "This Sample",
            color="#FF0000",
            fontsize=14,
            ha="right",
            va="top"                                
            )

        ax.set_xlabel("HRD probability", fontsize=14)
        ax.set_ylabel("")
        ax.set_yticks([])
        ax.set_xlim(0, max(probability_value, 1))
        ax.set_title("")

        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.subplots_adjust(right=0.7)

        ax.legend(
            title="",
            frameon=False,
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=12
            )

        plt.savefig(out_path, bbox_inches="tight", transparent=True)
        plt.close()

        return converter().convert_svg(out_path, 'HRD plot')

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
        Reads JSON from hrDetect and writes quartiles file for plotting
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
