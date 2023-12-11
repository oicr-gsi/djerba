"""Djerba plugin for CAPTIV-8 (research) reporting"""
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

        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        self.logger.debug("Specifying params for PARPi table plugin.")
        #discovered = [
        #  constants.DATA_MUTATIONS_FILE,
        #  constants.DATA_CNA_FILE,
        #  constants.DATA_EXPRESSION_FILE,
        #]
        #for key in discovered:
        #    self.add_ini_discovered(key)
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
                    if status == 0:
                        results[gene][constants.COPY_NUMBER] = 'Neutral'
                    elif status == -1:
                        results[gene][constants.COPY_NUMBER] = 'Heterozygous Deletion'
                    elif status == -2:
                        results[gene][constants.COPY_NUMBER] = 'Homozygous Deletion'
                    elif status > 0:
                        results[gene][constants.COPY_NUMBER] = 'Gain'
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
                    results[gene][constants.EXPRESSION_PERCENTILE] = float(exp)*100
        #for gene, values in results.items():
        #    if constants.EXPRESSION_PERCENTILE not in values:
        #        results[gene][constants.EXPRESSION_PERCENTILE] = 'None'

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
                var_class = row[8]
                if gene in constants.PARPI_GENES:
                    results[gene][constants.MUTATION_TYPE] = var_class

        # If the "Mutation Type" value didn't get updated, it means it wasn't in data_mutations_extended.txt.
        # So, update those with "None" as the mutation type.

        #for gene, values in results.items():
        #    if constants.MUTATION_TYPE not in values:
        #        results[gene][constants.MUTATION_TYPE] = 'None'
        return results
