"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import math
import json
import re
import logging

# For analysis
import pandas as pd
from scipy.stats import norm
import numpy as np
import matplotlib.pyplot as plt

from mako.lookup import TemplateLookup
from djerba.util.render_mako import mako_renderer
from djerba.plugins.base import plugin_base
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
import djerba.plugins.mrd_wisp.constants as pc
from djerba.util.image_to_base64 import converter
from matplotlib.lines import Line2D

class main(plugin_base):
    PRIORITY = 400
    PLUGIN_VERSION = '1.0'
    DICT = {True: "significantly larger", False: "not significantly larger"}

    def specify_params(self):
        #discovered = [
        #    pc.RESULTS_FILE,
        #]
        #for key in discovered:
        #    self.add_ini_discovered(key)
        
        self.add_ini_required(pc.RESULTS_FILE)
        self.add_ini_required(pc.ALL_TIMEPOINTS_DIR)
        self.add_ini_required("dates_list")

        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)

        # Get the summary file 
        if wrapper.my_param_is_null(pc.RESULTS_FILE):
            path_info = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
            results_path = path_info.get(pc.RESULTS_SUFFIX)
            if results_path == None:
                msg = 'Cannot find results path for WISP input'
                self.logger.error(msg)
                raise RuntimeError(msg)
            wrapper.set_my_param(pc.RESULTS_FILE, results_path)
        
        if wrapper.my_param_is_null(pc.ALL_TIMEPOINTS_DIR):
            msg = "Sorry, no fall-back right now. Manually supply this directory!"
            raise RuntimeError(msg)

        if wrapper.my_param_is_null("dates_list"):
            msg = "Sorry, no fall-back right now. Manually supply this directory!"
            raise RuntimeError(msg)


        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        output_dir = self.workspace.print_location()
        results_file = wrapper.get_my_string(pc.RESULTS_FILE)
        all_timepoints_dir = wrapper.get_my_string(pc.ALL_TIMEPOINTS_DIR)
        dates_list = wrapper.get_my_string("dates_list")

        # Get plugin data and plot MRD plot

        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        dates_list = [date.strip() for date in dates_list.split(",")]
        results = self.get_results(results_file, all_timepoints_dir, dates_list,output_dir)
        data[pc.RESULTS] = results
        
        # Read from the case_overview JSON file and populate results
        
        #json_file_path = os.path.join(workspace_dir, "pWGS_case_overview_output.json")
        
        #if os.path.exists(json_file_path):
        #    with open(json_file_path, 'r') as json_file:
        #        json_data = json.load(json_file)
        #        assay = json_data.get(pc.RESULTS, {}).get(pc.ASSAY, "Assay name not found")
        #        primary_cancer = json_data.get(pc.RESULTS, {}).get(pc.PRIMARY_CANCER, "Primary cancer not found")
        #        study_title = json_data.get(pc.RESULTS, {}).get(pc.STUDY, "Study title not found")
        #else:
        #    assay = "Assay name not found"
        #    primary_cancer = "Primary cancer not found"
        #    study_title = "Study title not found"

        #data[pc.RESULTS][pc.ASSAY] = assay
        #data[pc.RESULTS][pc.STUDY] = study_title
        #data[pc.RESULTS][pc.PRIMARY_CANCER] = primary_cancer

        return data 

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.ANALYSIS_TEMPLATE_NAME, data)
    
    def get_results(self, results_file, all_timepoints_dir, dates_list, output_dir):
        '''
        Extracts data and plots graph.
        Writes detection status to a file for the summary plugin.
        '''
        self.logger.info("Converting results file to dataframe and extracting data...")
        df = pd.read_csv(results_file, sep='\t')
        data = self.extract_data(df)
        self.logger.info("Extracted data from results file.")

        # Write detection status to a .txt file for the summary plugin to use:
        out_path = os.path.join(output_dir, pc.MRD_CALL_FILE)
        with open(out_path, "w") as file:
            file.write(str(data[pc.STATUS]))

        # Also write candidate SNVs (experimental)
        out_path = os.path.join(output_dir, 'candidate_snvs.txt')
        with open(out_path, "w") as file:
            file.write(str(data[pc.CANDIDATE_SITES]))

        # Plot detection plot
        self.logger.info("Generating MRD detection plot...")
        timepoints = self.initialize_timepoints(all_timepoints_dir, dates_list)
        self.make_plot_png(data, timepoints, output_dir)
        self.logger.info("Generated MRD detection plot")
        

        self.logger.info("Collecting plugin results...")
        results = data

        # Adding significance text based on the MRD call
        data[pc.SIGNIFICANCE] = self.DICT[data[pc.STATUS]]

        self.logger.info("Finished extracting MRD analysis.")


        # Experimental: adding all extracted WISP info to one row for the table after the report
        wisp_table_data = [] 
        bool_dict = {True: "Detected", False: "Not Detected"}
        for i, file in enumerate(sorted(os.listdir(all_timepoints_dir))):
            file_path = os.path.join(all_timepoints_dir, file)
            df = pd.read_csv(file_path, sep='\t')

            # Get data
            tumour = df.iloc[0] # First row is always the tumour sample

            wisp_table_data.append({
                pc.TIMEPOINT: dates_list[i],
                pc.WISP_DETECTION: bool_dict[bool(tumour["SNV_MRD"])],
                pc.WISP_TF: float(tumour["SNVPurity"])*100,
                pc.WISP_AF: int(tumour["AlleleFragments"])
            })

        data[pc.WISP_TABLE_DATA] = wisp_table_data

        return results
        
    
    def extract_data(self, df):
        '''
        Gets the following information:
        Sites detected column
        Sites detected column for normals only 
        Tumour cfDNA Donor ID (ex. ABC_0123)
        Tumour cfDNA MRD status (ex. True)
        Tumour cfDNA number of sites detected (int)
        Tumour cfDNA candidate sites passing QC (int)
        Tumour cfDNA mutant reads detected (int)
        Tumour cfDNA total reads checked (int)
        Tumour cfDNA read percentage, i.e. mutant/total reads * 100 (perc)
        '''

        # Tumour information is in the first row; the rest of the rows MAY be HBCs if HBCs were run.
        tumour = df.iloc[0]
    
        # Extract data from dataframe
    
        data = {}
        data[pc.NAME] = tumour['SampleId']
        data[pc.STATUS] = bool(tumour['SNV_MRD'])
        data[pc.TF] = tumour['SNVPurity']*100
        data[pc.SNV_LOD] = tumour['SNVLod']*100
        data[pc.CANDIDATE_SITES] = int(tumour['CalcVariants'])
        data[pc.ALLELE_FRAGMENTS] = int(tumour['AlleleFragments'])
        data[pc.TOTAL_FRAGMENTS] = int(tumour['TotalFragments'])
        
        return data
    

    def initialize_timepoints(self, all_timepoints_dir, dates_list):
        """
        All WISP summaries that will be plotted exist in results_folder.
        (This folder is created by the user for now; TO-DO to get these values from CouchDB)
        (TO-DO to get this to extract from report JSONS instead of SUMMARIES as report jsons have information like date of requisition).

        Will extract all information to make plot, no matter how many summaries (from 1 to n).
        If none, will throw error.
        """
        # Initialize input to plot
        timepoints = []

        for i, file in enumerate(sorted(os.listdir(all_timepoints_dir))):
            file_path = os.path.join(all_timepoints_dir, file)
            df = pd.read_csv(file_path, sep='\t')

            # Get data
            tumour = df.iloc[0] # First row is always the tumour sample

            timepoints.append({
                "timepoint_label": dates_list[i],
                "detected": bool(tumour["SNV_MRD"]),
                "tumour_fraction": float(tumour["SNVPurity"])*100,
                "limit_of_detection": float(tumour["SNVLod"])*100
            })

        # Convert to DataFrame
        timepoints = pd.DataFrame(timepoints)
        return timepoints

    def make_plot_png(self, data, timepoints, output_dir):
        """
        """

        # Generate plot
        fig, ax = self.plot_tumour_fraction(timepoints)

        # Save plot
        plot_path = os.path.join(output_dir, pc.DETECTION_PLOT)
        fig.savefig(plot_path, bbox_inches="tight")

        # Convert to base64
        image_converter = converter(self.log_level, self.log_path)
        b64txt = image_converter.convert_png(plot_path)
        
        # Add plot to output data
        data[pc.DETECTION_PLOT] = b64txt

        plt.close(fig)

        return data

    def plot_tumour_fraction(self, timepoints, max_timepoints=6, figsize=(9, 4)):
        """
        Plot tumour fraction over time, with timepoint 1 on the left.
    
        "timepoints" (df) has one row/array per timepoint, with columns:
            timepoint_label (string)    :  text on the x-axis (ex. T0, or dd-mm-yy, etc.)
            detected (bool)             :  True if MRD detected, False otherwise (sets the colour only)
            tumour_fraction (float)     :  tumour fraction in % (may be 0)
            limit_of_detection (float)  :  LOD in % (0 means no LOD to draw)
    
        The x-axis always has at least "max_timepoints" slots, so the plot stays
        the same size and unused slots on the right are simply blank.
    
        The y-axis is logarithmic, so a tumour fraction of exactly 0 cannot be
        plotted directly. Those timepoints are drawn on a reserved bottom row
        labelled "0". Every other timepoint is plotted at its real value.
        """
        
        
        # Get values and set detected/undetected colours
        is_detected = timepoints["detected"]
        has_positive_fraction = timepoints["tumour_fraction"] > 0 # TF = 0 makes log undefined        
        colours = np.where(is_detected, "red", "grey")
        
        
        # ------------------------------x-axis range start --------------------------------------
        # Changes string timepoints to be integer positions on the x-axis
        x_positions = np.arange(1, len(timepoints) + 1)
        # Maintain a minimum plot width equivalent to 6 timepoints; expand the plot if there are more than 6.
        # 6 was chosen as it makes a nice plot size.
        n_slots = max(max_timepoints, len(timepoints))
        # ------------------------------x-axis range end --------------------------------------
    
    
        # ------------------------------y-axis range start --------------------------------------
        # Work out the y-axis range from positive values only (zeros can't be on a log axis)
        # Makes a panda series that's just TF > 0 and LOD > 0
        positive_values = pd.concat([
            timepoints.loc[timepoints["limit_of_detection"] > 0, "limit_of_detection"],
            timepoints.loc[has_positive_fraction, "tumour_fraction"],
        ])
        
        # A log scale goes by powers of 10
        # To determine min and max limits of the y-axis, need highest and lowest powers of 10
        lowest_power = int(np.floor(np.log10(positive_values.min()))) - 1 if len(positive_values) else -3 # 0.001
        highest_power = (int(np.ceil(np.log10(positive_values.max()))) if len(positive_values) else lowest_power + 3) # 100 
        
        # Zeros are drawn on the reserved bottom row; everything else at its real value
        zero_row_level = 10.0 ** lowest_power
        plot_tumour_fraction = timepoints["tumour_fraction"].where(has_positive_fraction, zero_row_level)
        # ------------------------------y-axis range end --------------------------------------
    
    
        # ------------------------------ main plotting start ---------------------------------- 
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_yscale("log")
        

        # Shaded "below limit of detection" region: from the bottom of the plot up to the LOD.
        # Timepoints with LOD = 0 drop to the bottom (no shading). Extended half a slot either side.
        y_bottom = 10.0 ** (lowest_power - 0.5)
        lod = timepoints["limit_of_detection"]
        lod_top = np.where(lod > 0, lod, y_bottom)
        lod_x = np.concatenate([[x_positions[0] - 0.5], x_positions, [x_positions[-1] + 0.5]])
        lod_y = np.concatenate([[lod_top[0]], lod_top, [lod_top[-1]]])
        ax.fill_between(lod_x, y_bottom, lod_y, color="#cccccc", linewidth=0, zorder=0)

        # Small tick at each LOD value
        has_lod = lod > 0
        ax.scatter(x_positions[has_lod], lod[has_lod], marker="s", s=6, color="grey", zorder=3)

        # Points
        ax.scatter(x_positions, 
                   plot_tumour_fraction, 
                   c=colours, 
                   s=80, 
                   edgecolor="black", 
                   zorder=2 # zorder=3 makes the line appear BEHIND the dot
        ) 
    
        # Line joining the points
        ax.plot(x_positions, 
                plot_tumour_fraction, 
                color="grey", 
                linewidth=1.5, 
                zorder=1
        )
    
        # TF value above each detected timepoint only (coloured to match its point)
        labelled_rows = timepoints[is_detected]
        labelled_colours = colours[is_detected]
        for x, fraction, colour in zip(x_positions[is_detected], labelled_rows["tumour_fraction"], labelled_colours):
            ax.annotate(f"{fraction:.3g}", (x, fraction),
                        textcoords="offset points", xytext=(0, 10),
                        ha="center", color=colour, fontsize=8, fontweight="bold")        
        # ------------------------------ main plotting end --------------------------------------
    
        
        # ------------------------------ axes and legend start ----------------------------------
        # Axes: fixed slots on x, powers of ten on y with the bottom tick as "0"
        ax.set_xlim(0.5, n_slots + 0.5)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(timepoints["timepoint_label"].to_list(), fontsize=8)
    
        powers = np.arange(lowest_power, highest_power + 1)
        ax.set_yticks(10.0 ** powers)
        ax.set_yticklabels(["0"] + [f"{10.0 ** p:g}" for p in powers[1:]], fontsize=8)
        ax.set_ylim(10.0 ** (lowest_power - 0.5), 10.0 ** (highest_power + 0.3))
        ax.minorticks_off()
    
        ax.set_ylabel("Tumour Fraction (%)")
        ax.set_xlabel("Timepoint")
        ax.grid(axis="y", color="lightgrey", linewidth=0.7)
        ax.spines[["top", "right"]].set_visible(False)
        
        # Legend
        legend_entries = [
            Line2D([], [], marker="o", linestyle="", markerfacecolor="red", markeredgecolor="black", label="MRD Detected"),
            Line2D([], [], marker="o", linestyle="", markerfacecolor="grey", markeredgecolor="black", label="MRD Not Detected"),
            Line2D([], [], color="grey", linestyle=":", label="Limit of detection"),
        ]
        ax.legend(handles=legend_entries, loc="upper center", bbox_to_anchor=(0.5, -0.3),
                  ncol=3, frameon=False, fontsize=8)
    
        fig.tight_layout()
        # ------------------------------ axes and legend end --------------------------------------
    
        return fig, ax
