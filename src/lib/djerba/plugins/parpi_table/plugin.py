"""Djerba plugin for PARPi table (research) reporting"""
import os
import sys
import csv
import gzip
import logging
import json
import subprocess
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
import djerba.plugins.parpi_table.constants as constants
from djerba.plugins.base import plugin_base
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer
from djerba.util.environment import directory_finder

class main(plugin_base):

    PRIORITY = 2000
    PLUGIN_VERSION = '1.0'
    TEMPLATE_NAME = 'template.html'
 
    def configure(self, config):

        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)

        # This plugin requires three files already created earlier:
        # - data_mutations_extended.txt
        # - data_CNA.txt
        # - data_expression_percentile_tcga.txt
        
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
      
        # Get starting plugin data
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
       
        # Get paths to files.
        work_dir = self.workspace.get_work_dir()
        mutations_file = os.path.join(work_dir, constants.DATA_MUTATIONS_TXT)
        cna_file = os.path.join(work_dir, constants.DATA_CNA_TXT)
        expression_file = os.path.join(work_dir, constants.DATA_EXPRESSION_TXT)

        # Initialize the results dictionary that will contain information about all the genes.
        results = {}
        for gene in constants.PARPI_GENES:
            results[gene] = {}
        
        # Update results with mutation type.
        results = self.get_mutation_type(mutations_file, results)

        # Update results with copy number.
        results = self.get_copy_number(cna_file, results)

        # Update results with expression.
        results = self.get_expression(expression_file, results)

        # Add an extra column that puts an X if it is to be brought to attention.
        results = self.add_X_marker(results)

        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        self.logger.debug("Specifying params for PARPi table plugin.")
        self.set_ini_default(core_constants.ATTRIBUTES, 'research')
        self.set_priority_defaults(self.PRIORITY)


    def get_copy_number(self, cna_path, results):

        with open(cna_path) as cna_file:
            reader = csv.reader(cna_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                gene = row[0]
                status = int(row[1])
                if gene in constants.PARPI_GENES:
                    if status == 2:
                        results[gene][constants.COPY_NUMBER] = 'Amplification'
                    elif status == -2:
                        results[gene][constants.COPY_NUMBER] = 'Deletion'
                    else:
                        results[gene][constants.COPY_NUMBER] = 'None'
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
                if gene in constants.PARPI_GENES:
                    results[gene][constants.EXPRESSION_PERCENTILE] = round(float(exp)*100, 1)

        return results

    def get_mutation_type(self, mut_path, results):

        with open(mut_path) as mut_file:
            reader = csv.reader(mut_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                gene = row[0]
                var_class = row[8].replace("_", " ")
                if gene in constants.PARPI_GENES:
                    results[gene][constants.MUTATION_TYPE] = var_class

        return results
    
    def add_X_marker(self, results):

        for gene, value in results.items():
            
            # MUTATION: Only check if True == True
            mutation_1 = constants.MUTATION_TYPE in results[gene] # True if mutation, False if no mutation
            mutation_2 = constants.PARPI_GENES[gene].get(constants.MUTATION_TYPE) # True if mutation, None if not relevant
            
            # COPY NUMBER: Check if Gain == Gain, Homozygous Deletion == Homozygous Deletion, etc.
            copy_number_1 = results[gene].get(constants.COPY_NUMBER, False) # If not, will be False
            copy_number_2 = constants.PARPI_GENES[gene].get(constants.COPY_NUMBER) # If not, will be None
            
            # EXPRESSION: Check if expression <= 10% if expression is a relevant criteria 
            expression_1 = results[gene].get(constants.EXPRESSION_PERCENTILE, 100) # If not, will be 100
            expression_2 = constants.PARPI_GENES[gene].get(constants.EXPRESSION_PERCENTILE, False) # If not, will be False

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
