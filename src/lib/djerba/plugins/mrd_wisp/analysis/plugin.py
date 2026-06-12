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

class main(plugin_base):
    PRIORITY = 200
    PLUGIN_VERSION = '1.0'
    DICT = {True: "significantly larger", False: "not significantly larger"}

    def specify_params(self):
        discovered = [
            pc.RESULTS_FILE,
        ]
        for key in discovered:
            self.add_ini_discovered(key)
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
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        output_dir = self.workspace.print_location()
        results_file = wrapper.get_my_string(pc.RESULTS_FILE)

        # Get plugin data and plot PWGS plot

        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        results = self.get_results(results_file, output_dir)
        data[pc.RESULTS] = results
        
        workspace_dir = self.workspace.get_work_dir()
        

        # Read from the case_overview JSON file and populate results
        
        json_file_path = os.path.join(workspace_dir, "pWGS_case_overview_output.json")
        
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                json_data = json.load(json_file)
                assay = json_data.get(pc.RESULTS, {}).get(pc.ASSAY, "Assay name not found")
                primary_cancer = json_data.get(pc.RESULTS, {}).get(pc.PRIMARY_CANCER, "Primary cancer not found")
                study_title = json_data.get(pc.RESULTS, {}).get(pc.STUDY, "Study title not found")
        else:
            assay = "Assay name not found"
            primary_cancer = "Primary cancer not found"
            study_title = "Study title not found"

        data[pc.RESULTS][pc.ASSAY] = assay
        data[pc.RESULTS][pc.STUDY] = study_title
        data[pc.RESULTS][pc.PRIMARY_CANCER] = primary_cancer

        return data 


    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(pc.ANALYSIS_TEMPLATE_NAME, data)
    
    def get_results(self, results_file, output_dir):
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
        data = self.calculate_detection_cutoff(data)
        data = self.make_detection_plot(data, output_dir)
        self.logger.info("Generated MRD detection plot")
        
        self.logger.info("Collecting plugin results...")
        results = data

        # Adding significance text based on the MRD call
        data[pc.SIGNIFICANCE] = self.DICT[data[pc.STATUS]]

        # Ommiting some pandas series from the results dictionary so they don't end up in the json.
        del results[pc.ALL_SITES_DETECTED]
        del results[pc.HBC_SITES_DETECTED]

        self.logger.info("Finished extracting MRD analysis.")

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
    
    
        # Get sites detected as a column
        # Note: Hartwig defines "sites detected" as the sum of "Frag1Variants" and "Frag2PlusVariants"
        df['SitesDetected'] = df['Frag1Variants'] + df['Frag2PlusVariants']
    
        # Tumour information is in the first row; the rest of the rows are healthy blood controls ("normals")
        tumour = df.iloc[0]
        normals = df['SitesDetected'][1:].to_numpy() # only need sites detected
    
        # Extract data from dataframe
    
        data = {}
        data[pc.ALL_SITES_DETECTED] = df['SitesDetected']
        data[pc.HBC_SITES_DETECTED] = normals
        data[pc.NAME] = tumour['sample_id']
        data[pc.STATUS] = bool(tumour['SNV_MRD'])
        data[pc.TUMOUR_SITES_DETECTED] = int(tumour['SitesDetected'])
        data[pc.CANDIDATE_SITES] = int(tumour['CalcVariants'])
        data[pc.READS_DETECTED] = int(tumour['AlleleFragments'])
        data[pc.READS_CHECKED] = int(tumour['TotalFragments'])
        data[pc.READ_PERCENTAGE] = round(float(data[pc.READS_DETECTED]/data[pc.READS_CHECKED]*100), 2)
        
        return data
    
    
    def calculate_detection_cutoff(self, data):
        '''
        Calculates detection cut-off for the purpose of plotting.
        It back-calculates this cut-off by projecting the p-value cut-off onto the z-distribution of detected sites.
        '''
        # Calculating detection cutoff
        pvalue_cutoff = pc.DETECTION_ALPHA
        all_sites_detected = data[pc.ALL_SITES_DETECTED]
    
        # The detection cutoff is back-calculated from the p-value.
        # I.e. the p-value is mapped onto the distribution to "convert" it to detected number of sites
        z = norm.ppf(1 - pvalue_cutoff)
        m = np.mean(all_sites_detected)
        std = np.std(all_sites_detected)
        detection_cutoff = m + (std*z)
        
        data[pc.DETECTION_CUTOFF] = float(detection_cutoff)
        return data
    
    def make_detection_plot(self, data, output_dir):
        '''
        Generates the plot showing detected number of sites in the plasma compared to a box plot of healthy blood controls.
        '''
    
        # Generate figure
        fig, ax = plt.subplots(figsize=(8, 2))
    
        # Box plot of normals
        ax.boxplot(data[pc.HBC_SITES_DETECTED], vert=False, positions=[0], widths=0.3,
                   patch_artist=False, showfliers=False,
                   medianprops=dict(color='gray'),
                   boxprops=dict(color='gray'),
                   whiskerprops=dict(color='gray'),
                   capprops=dict(color='gray'))
    
        ## Dots on top of box plot
    
        # Add individual normal points
        y_jitter = np.random.normal(0, 0.03, size=len(data[pc.HBC_SITES_DETECTED]))
    
        ax.scatter(
            data[pc.HBC_SITES_DETECTED],
            y_jitter,
            color='gray',
            alpha=0.7,
            s=20,
            zorder=4
        )

        median = np.median(data['hbc_detected_sites'])
        ax.text(median, -0.25, f'Control Cohort', color='gray', fontsize=8, va='top', ha='center')

        # Threshold line
        ax.axvline(data[pc.DETECTION_CUTOFF], color='gray', linestyle='--', linewidth=1)
        ax.text(data[pc.DETECTION_CUTOFF], 0.25, f'Detection Cutoff: {int(np.ceil(data[pc.DETECTION_CUTOFF]))} sites',
                color='gray', fontsize=8, va='bottom', ha='center')
    
        # Tumour point
        ax.scatter(data[pc.TUMOUR_SITES_DETECTED], 0, color='red', s=80, zorder=5)
        ax.text(data[pc.TUMOUR_SITES_DETECTED], -0.25, f'This Sample: {round(data[pc.TUMOUR_SITES_DETECTED])} sites',
                color='red', fontsize=8, va='top', ha='center')
    
        # Clean up axes
        ax.set_yticks([])
        ax.spines[['left', 'top', 'right']].set_visible(False)
        ax.set_xlabel('Detected Sites')
    
        plt.tight_layout()
        plot_path = os.path.join(output_dir, pc.DETECTION_PLOT)
        plt.savefig(plot_path)
        image_converter = converter(self.log_level, self.log_path)
        b64txt = image_converter.convert_png(plot_path)
        data[pc.DETECTION_PLOT] = b64txt
        return data
