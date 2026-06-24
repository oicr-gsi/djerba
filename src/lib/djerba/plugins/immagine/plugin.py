"""Djerba plugin for the Immagine (MyC) reporting table (research) reporting"""
import os
import sys
import csv
import gzip
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
            'seg_file',
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

        wrapper = self.update_wrapper_if_null(wrapper, 'seg_file_immagine', 'seg_file')

        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
      
        # Get starting plugin data
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
       
        # Get paths to files.
        work_dir = self.workspace.get_work_dir()
        mutations_file = os.path.join(work_dir, constants.DATA_MUTATIONS_TXT)
        seg_file = config[self.identifier]['seg_file']
        #seg_file = "/.mounts/labs/CGI/scratch/aalam/immagine/MYC-3171/report/MYC_0358_Bm_P_MyC-358-T0-OZ.solPrimary.purple/MYC_0358_Bm_P_MyC-358-T0-OZ.purple.cnv.somatic.tsv"
        
        seg_df = pd.read_csv(seg_file, sep = '\t')
        cna_file = os.path.join(work_dir, constants.DATA_CNA_TXT)
        expression_file = os.path.join(work_dir, constants.DATA_EXPRESSION_TXT)

        # Initialize the results dictionary that will contain information about all the genes.
        results = {}
    
        # Update results with cytogenetic alterations table information.
        results = self.get_cytogenetic_alterations(seg_df, results)

        for gene in constants.GENES:
            results[gene] = {}
        
        # Update results with mutation type.
        results = self.get_mutation_type_and_alt(mutations_file, results)

        # Update results with copy number.
        results = self.get_copy_number(cna_file, results)

        # Update results with expression.
        results = self.get_expression(expression_file, results)
        
        results = self.get_p53_alt(results)

        results = self.get_high_risk_myeloma(results)

        # Add an extra column that puts an X if it is to be brought to attention.
        #results = self.add_X_marker(results)

        data['results'] = results




        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
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
        mutation_of_tp53 = results['TP53']
        biallelic_del_1p32 = results[constants.CYTOGEN_ALTS][constants.BI_DEL_1P32]

        # Group B: any two
        translocation_chr14 = False #results[constants.TRANSLOCATIONS][idk]
        gain_or_amp_1q = results[constants.CYTOGEN_ALTS][constants.AMP_1P]
        monoallelic_del_1p32 = results[constants.CYTOGEN_ALTS][constants.MONO_DEL_1P32]

        high_risk_group_A = [chromosome_17p_deletion, mutation_of_tp53, biallelic_del_1p32]
        high_risk_group_B = [translocation_chr14, gain_or_amp_1q, monoallelic_del_1p32]

        high_risk = any(high_risk_group_A) or sum(high_risk_group_B)>=2

        results[constants.HIGH_RISK] = high_risk

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
        data[constants.AMP_1P] = cytogen_alts.chromosome_1p_gain_or_amp(seg_df)
        data[constants.HYPERDIPLOIDY] = cytogen_alts.hyperdiploidy(seg_df)
        data[constants.BI_DEL_1P32] = cytogen_alts.biallelic_1p32_deletion(seg_df)
        data[constants.MONO_DEL_1P32] = cytogen_alts.monoallelic_1p32_deletion(seg_df)

        results[constants.CYTOGEN_ALTS] = data


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

    def get_copy_number(self, cna_path, results):

        with open(cna_path) as cna_file:
            reader = csv.reader(cna_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                gene = row[0]
                #status = int(row[1])
                status = int(row[2])
                if gene in constants.GENES:
                    if status == 2:
                        results[gene][constants.COPY_NUMBER] = 'Amplification'
                    elif status == -2:
                        results[gene][constants.COPY_NUMBER] = 'Deletion'
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
                    results[gene][constants.EXPRESSION_PERCENTILE] = round(float(exp)*100, 1)

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
    
    def add_X_marker(self, results):

        for gene, value in results.items():
            
            # MUTATION: Only check if True == True
            mutation_1 = constants.MUTATION_TYPE in results[gene] # True if mutation, False if no mutation
            mutation_2 = constants.GENES[gene].get(constants.MUTATION_TYPE) # True if mutation, None if not relevant
            
            # COPY NUMBER: Check if Gain == Gain, Homozygous Deletion == Homozygous Deletion, etc.
            copy_number_1 = results[gene].get(constants.COPY_NUMBER, False) # If not, will be False
            copy_number_2 = constants.GENES[gene].get(constants.COPY_NUMBER) # If not, will be None
            
            # EXPRESSION: Check if expression <= 10% if expression is a relevant criteria 
            expression_1 = results[gene].get(constants.EXPRESSION_PERCENTILE, 100) # If not, will be 100
            expression_2 = constants.GENES[gene].get(constants.EXPRESSION_PERCENTILE, False) # If not, will be False

            if (mutation_1 and mutation_2) or (copy_number_1 == copy_number_2):
                results[gene][constants.CHECKMARK] = "X"
            elif expression_2: # if one requirement is that expression is below 10%
                if expression_1 <= 10:
                    results[gene][constants.CHECKMARK] = "X"
                else:
                    results[gene][constants.CHECKMARK] = ""
            else:
                results[gene][constants.CHECKMARK] = ""
        return results
