"""Djerba plugin for the Immagine (MyC) reporting table (research) reporting"""
import os
import sys
import csv
import gzip
import zipfile
import logging
import json
import subprocess
import pandas as pd
import numpy as np
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
import djerba.plugins.immagine.constants as constants
import djerba.plugins.immagine.cytogen_alts as cytogen_alts
from djerba.plugins.base import plugin_base
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer
from djerba.util.environment import directory_finder

class main(plugin_base):

    PRIORITY = 2000
    PLUGIN_VERSION = '1.0'
    TEMPLATE_NAME = 'template.html'


    def specify_params(self):
        discovered = [
            constants.SBS_FILE,
            constants.PURPLE_CNV_GENE_FILE,
            constants.IGCALLER_FILE
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'research')
        self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):

        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)

        # This plugin requires three files already created earlier:
        # - data_mutations_extended.txt
        # - purple.data_CNA.txt
        # - data_expression_percentile_tcga.txt
        
        wrapper = self.get_config_wrapper(config)
        dpi = core_constants.DEFAULT_PATH_INFO
        wrapper = self.update_wrapper_if_null(wrapper, dpi, constants.SBS_FILE, constants.SBS_WORKFLOW)
        # THIS WILL NEED UPDATING TO FIND THE RIGHT FILE FROM WORKSPACE OR SOMETHING.
        # Giving manually for now.
        wrapper = self.update_wrapper_if_null(wrapper, dpi, constants.PURPLE_CNV_GENE_FILE, constants.SBS_WORKFLOW)
        wrapper = self.update_wrapper_if_null(wrapper, dpi, constants.IGCALLER_FILE, constants.SBS_WORKFLOW)

        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
      
        # Get starting plugin data
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
       
        # Initialize results dictionary
        results = {}

        # Get paths to files.
        work_dir = self.workspace.get_work_dir()
        finder = directory_finder()
        self.r_script_dir = finder.get_base_dir() + "/plugins/immagine/Rscripts/"
        mutations_file = os.path.join(work_dir, constants.DATA_MUTATIONS_TXT)
        seg_file = os.path.join(work_dir, constants.PURPLE_SEGMENTS_FILE)
        seg_df = self.process_seg_file(seg_file)
        #cna_file = os.path.join(work_dir, constants.DATA_CNA_TXT)
        cna_file = config[self.identifier][constants.PURPLE_CNV_GENE_FILE]
        igcaller_results = config[self.identifier][constants.IGCALLER_FILE]
        ploidy = float(self.workspace.read_json(constants.PURITY_PLOIDY_JSON)['ploidy'])
        hrdetect_sbs_json = config[self.identifier][constants.SBS_FILE]
        if self.workspace.has_file(constants.DATA_EXPRESSION_TXT):
            expression_file = os.path.join(work_dir, constants.DATA_EXPRESSION_TXT)
            results[constants.HAS_EXPRESSION_DATA] = True
        else:
            results[constants.HAS_EXPRESSION_DATA] = False 

        # Update results with cytogenetic alterations table information.
        results = self.get_cytogenetic_alterations(seg_df, results)

        for gene in constants.GENES:
            results[gene] = {}
        
        # Update results with translocations.
        results = self.get_translocations(igcaller_results, results)

        # Update results with mutation type.
        results = self.get_mutation_type_and_alt(mutations_file, results)

        # Update results with copy number.
        results = self.get_copy_number(cna_file, ploidy, results)

        # Update results with expression.
        if results[constants.HAS_EXPRESSION_DATA]:
            results = self.get_expression(expression_file, results)
        
        results = self.get_p53_alt(results)

        results = self.get_apobec_signatures(hrdetect_sbs_json, results)

        results = self.get_high_risk_myeloma(results)

        data['results'] = results

        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
   
    def process_seg_file(self, seg_file):
        """
        Rounds copyNumber both to 0 decimal places and 1 decimal place, and returns a dataframe.
        0 decimal places: for evaluating statements like "CN >= 3"
        1 decimal place: for exaluating statements like "CN >= 1.5"
        """
        seg_df = pd.read_csv(seg_file, sep = '\t')
        seg_df['copyNumber_round_int'] = round(seg_df['copyNumber'])
        seg_df['copyNumber_round_1dec'] = round(seg_df['copyNumber'], 1)
        return seg_df

    def get_high_risk_myeloma(self, results):
        """
        A patient meets the definition for high risk myeloma if they have any one of:
        - Chromosome 17p deletion
        - Mutation of TP53
        - Biallelic deletion of 1p32

        OR

        Any two of:
        - Any one of: t(4;14), t(14;16), or t(14;20) <-- for now, ignore
        - Gain or amplification of chromosome 1q
        - Monoallelic deletion of 1p32
        """

        # Group A: any one
        chromosome_17p_deletion = results[constants.CYTOGEN_ALTS][constants.DEL_17P]
        mutation_of_tp53 = results[constants.P53_ALT]
        biallelic_del_1p32 = results[constants.CYTOGEN_ALTS][constants.BI_DEL_1P32]

        #print("17p del ", chromosome_17p_deletion)
        #print("tp53 ", mutation_of_tp53)
        #print("biallelic del 1p32 ", biallelic_del_1p32)

        # Group B: any two
        translocation = any(results[constants.TRANSLOCATIONS].get(x, False) for x in [constants.t4_14, constants.t14_16, constants.t14_20])
        results[constants.HIGH_RISK_TRANSLOC] = translocation
        gain_or_amp_1q = results[constants.CYTOGEN_ALTS][constants.AMP_1P]
        monoallelic_del_1p32 = results[constants.CYTOGEN_ALTS][constants.MONO_DEL_1P32]

        #print("translocation default false ", translocation_chr14)
        #print("gain amp 1q ", gain_or_amp_1q)
        #print("monoallelic del 1p32 ", monoallelic_del_1p32)

        high_risk_group_A = [chromosome_17p_deletion, mutation_of_tp53, biallelic_del_1p32]
        high_risk_group_B = [translocation, gain_or_amp_1q, monoallelic_del_1p32]

        #print("A ", high_risk_group_A)
        #print("B ", high_risk_group_B)

        high_risk = any(high_risk_group_A) or sum(high_risk_group_B)>=2

        #print("risk ", high_risk)

        results[constants.HIGH_RISK] = high_risk

        return results

    def get_apobec_signatures(self, hrdetect_sbs_json, results):
        """
        Extracts cosmic signatures SBS2 and SBS13 from the .exposures.SBS.json file which is outputted from HRDetect.
        The file has either a 0 or a score.
        For simplicity, this function returns "present" for a score > 0 and "absent" for a score = 0.
        """
        
        data = self.workspace.read_json(hrdetect_sbs_json)
        exposures = data['exposures'][0]
        apobec_sigs = {name: exposures[name] != 0 for name in ('SBS2', 'SBS13')}
        results[constants.APOBEC_SIGS] = apobec_sigs
        return results

    def get_cytogenetic_alterations(self, seg_df, results):
        """
        Returns a dictionary like:

        {
        monosomy_17: True,
        monosomy_13: False,
        hyperdiploidy: False,
        etc...
        }

        """

        data = {}

        data[constants.MONOSOMY_13] = cytogen_alts.monosomy("chr13", seg_df)
        data[constants.MONOSOMY_14] = cytogen_alts.monosomy("chr14", seg_df)
        data[constants.MONOSOMY_17] = cytogen_alts.monosomy("chr17", seg_df)
        data[constants.DEL_1P] = cytogen_alts.chromosome_1p_deletion(seg_df)
        data[constants.DEL_17P] = cytogen_alts.chromosome_17p_deletion(seg_df)
        data[constants.AMP_1Q] = cytogen_alts.chromosome_1q_gain_or_amp(seg_df)
        data[constants.AMP_1P] = cytogen_alts.chromosome_1p_gain_or_amp(seg_df)
        data[constants.HYPERDIPLOIDY] = cytogen_alts.hyperdiploidy(seg_df)
        data[constants.BI_DEL_1P32] = cytogen_alts.biallelic_1p32_deletion(seg_df)
        data[constants.MONO_DEL_1P32] = cytogen_alts.monoallelic_1p32_deletion(seg_df)

        results[constants.CYTOGEN_ALTS] = data

        print(results[constants.CYTOGEN_ALTS])

        return results

    def get_p53_alt(self, results):
        """
        Return True if any of the following are true:
        - There is a TP53 amplification
        - There is a TP53 deletion
        - There is a TP53 SNV (any)
        """

        tp53 = results.get("TP53", {})

        cnv = constants.COPY_NUMBER in tp53
        snv = constants.MUTATION_FOUND in tp53
        
        results[constants.P53_ALT] = cnv or snv

        return results 

    def get_copy_number(self, cna_file, ploidy, results):
        """
        Gets copy number (rounded) from the .purple.cnv.gene.tsv file for relevant genes.
        """
        cna_df = pd.read_csv(cna_file, sep = '\t')

        # Round the min and max copy numbers
        cna_df['minCopyNumber_round_int'] = round(cna_df['minCopyNumber'])
        cna_df['maxCopyNumber_round_int'] = round(cna_df['maxCopyNumber'])

        cna_df.to_csv(r'/.mounts/labs/CGI/scratch/aalam/immagine/igcaller/MYC_0160/report/testing.txt', sep = '\t')
        # Only keep genes in list
        subset_cna_df = cna_df[cna_df["gene"].isin(constants.GENES)]

        # Thresholds
        amp = ploidy * 2.4
        gain = ploidy * 1.4
        htzdel = ploidy * 0.6
        hmzdel = 0.5

        # Loop through
        for i, row in subset_cna_df.iterrows():
            gene = row["gene"]
            min_CN = row["minCopyNumber"]
            max_CN = row["maxCopyNumber"]
            if min_CN < hmzdel: # look at min for deletion
                results[gene][constants.COPY_NUMBER] = 'DELETION'
            elif min_CN < htzdel:
                results[gene][constants.COPY_NUMBER] = 'DELETION'
            elif max_CN > gain and min_CN < amp: # for partial amps (gains), HMF uses the max_CN not the min_CN
                results[gene][constants.COPY_NUMBER] = 'GAIN'
            elif min_CN >= amp: 
                results[gene][constants.COPY_NUMBER] = 'AMP'

        return results



    def get_expression(self, exp_path, results):

        with open(exp_path) as exp_file:
            reader = csv.reader(exp_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                gene = row[0]
                exp = row[1]
                if gene in constants.GENES:
                    #results[gene][constants.EXPRESSION_PERCENTILE] = round(float(exp)*100, 1)
                    results[gene][constants.EXPRESSION_PERCENTILE] = round(float(exp), 1)

        return results

    def get_mutation_type_and_alt(self, mut_path, results):

        with open(mut_path) as mut_file:
            reader = csv.reader(mut_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                gene = row[0]
                var_class = row[8].replace("_", " ")
                alt = row[36]
                if pd.isnull(alt):
                    alt = row[34]
                if pd.isnull(alt):
                    pass
                    # return an error idk
                if gene in constants.GENES:
                    results[gene][constants.MUTATION_FOUND] = True
                    results[gene][constants.MUTATION_TYPE] = var_class
                    results[gene][constants.MUTATION_ALT] = alt


        return results

    def get_translocations(self, igcaller_results, results):
        """
        Gets the various IG translocation using igcaller outputs that have been run through an R script.
        This function only cares if ANY translocation with a score above 100 exists with those chromosomes.
        It doesn't care what gene, locus, etc.
        That filtering has already been done in the R script.
        """

        # Unzip the igcaller results
        igcaller_results_unzipped = self.unzip_igcaller_results(igcaller_results)
        x = self.run_igcaller_postprocess(igcaller_results_unzipped)
        print(x)
        translocation_path = os.path.join(self.workspace.get_work_dir(), constants.COMMON_IGCALLS)
        df = pd.read_csv(translocation_path, sep='\t')
        df = df[df['IGCaller_Score'] >= 100]

        # Write the t notation, ex. t(14;16)
        df['t_notation'] = (
            "t("
            + df['break1_chromosome'].str.replace('chr', '')
            + ";"
            + df['break2_chromosome'].str.replace('chr', '')
            + ")"
        )

        found_translocations = df["t_notation"].unique().tolist()
        translocations = {constants.IGH: [
                             constants.t4_14,
                             constants.t14_16,
                             constants.t14_20,
                             constants.t8_14,
                             constants.t11_14,
                             constants.t6_14],
                          constants.IGK: [
                             constants.t2_8],
                          constants.IGL: [
                             constants.t8_22]
        }


        found_translocations = df["t_notation"].unique()
        final_translocations = {}

        for locus, events in translocations.items():
            for event in events:
                if event in found_translocations:
                    final_translocations[locus] = True
                    final_translocations[event] = True

        results[constants.TRANSLOCATIONS] = final_translocations
        return results

    def run_igcaller_postprocess(self, igcaller_results):
        """
        Runs the R script from Dory Abelman that does some post-processing and further filtering of the igcaller results.
        """

        cmd = [
            'Rscript', self.r_script_dir + "/filter_igcaller.R",
            '--base_dir', self.r_script_dir,
            '--raw_igcaller_dir', igcaller_results,
            '--cytoband_file', self.r_script_dir + "/cytoBand.txt",
            '--blacklist_bed', self.r_script_dir + "/hg38-blacklist.v2.bed",
            '--output_dir', self.workspace.get_work_dir()
        ]

        runner = subprocess_runner()
        result = runner.run(cmd, "main R script")
        return result

    def unzip_igcaller_results(self, igcaller_zip):
        """
        Extracts the zipped igcaller results directory in the workspace 
        """
        with zipfile.ZipFile(igcaller_zip) as zf:
            extract_dir = os.path.join(self.workspace.get_work_dir(), os.path.splitext(os.path.basename(igcaller_zip))[0])
        zf.extractall(extract_dir)

        return extract_dir
