"""
Plugin to generate the Fusions report section
"""

import csv
import logging
import os
import re
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.fusion.tools import fusion_reader, prepare_fusions
from djerba.util.environment import directory_finder
from djerba.util.html import html_builder as hb
from djerba.util.logger import logger
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb
import djerba.plugins.fusion.constants as fc
import json
import base64
import pysam

class main(plugin_base):
    PRIORITY = 900
    PLUGIN_VERSION = '1.1.0'
    CACHE_DEFAULT = '/.mounts/labs/CGI/gsi/tools/djerba/oncokb_cache/scratch'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper = self.update_file_if_null(wrapper, fc.ARRIBA_PATH, 'arriba')
        wrapper = self.update_file_if_null(wrapper, fc.MAVIS_PATH, 'mavis')
        self.update_wrapper_if_null(wrapper, 'input_params.json', fc.ONCOTREE_CODE, 'oncotree_code')
        if wrapper.my_param_is_null(core_constants.TUMOUR_ID):
            sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            wrapper.set_my_param(core_constants.TUMOUR_ID, sample_info.get(core_constants.TUMOUR_ID))
        return wrapper.get_config()

    def extract(self, config):
        def sort_by_actionable_level(row):
            return oncokb_levels.oncokb_order(row[core_constants.ONCOKB])

        wrapper = self.get_config_wrapper(config)
        prepare_fusions(self.workspace.get_work_dir(), self.log_level, self.log_path).process_fusion_files(wrapper)
        fus_reader = fusion_reader(self.workspace.get_work_dir(), self.log_level, self.log_path)
        total_fusion_genes = fus_reader.get_total_fusion_genes()
        gene_pair_fusions = fus_reader.get_fusions()
        if gene_pair_fusions is not None:
            outputs = fus_reader.fusions_to_json(gene_pair_fusions, wrapper.get_my_string(fc.ONCOTREE_CODE))
            [rows, gene_info, treatment_opts] = outputs
            # Sort by OncoKB level
            rows = sorted(rows, key=sort_by_actionable_level)
            max_actionable = oncokb_levels.oncokb_order('P')
            rows = list(filter(lambda x: oncokb_levels.oncokb_order(x[core_constants.ONCOKB]) <= max_actionable, rows))
            results = {
                fc.TOTAL_VARIANTS: total_fusion_genes,
                fc.CLINICALLY_RELEVANT_VARIANTS: fus_reader.get_total_oncokb_fusions(),
                fc.NCCN_RELEVANT_VARIANTS: fus_reader.get_total_nccn_fusions(),
                fc.BODY: rows
            }
        else:
            results = {
                fc.TOTAL_VARIANTS: 0,
                fc.CLINICALLY_RELEVANT_VARIANTS: 0,
                fc.NCCN_RELEVANT_VARIANTS: 0,
                fc.BODY: []
            }
            gene_info = []
            treatment_opts = []

        # Processing fusions and generating blob URLs
        tsv_file_path = wrapper.get_my_string(fc.ARRIBA_PATH)
        json_template_path = 'fusion_template_to_be_compressed.json'
        output_dir = self.workspace.get_work_dir()
        unique_fusions = list({item["fusion"] for item in results[fc.BODY]})
        fusion_url_pairs = []

        for fusion in unique_fusions:
            try:
                fusion, blurb_url = self.process_fusion(fusion, tsv_file_path, json_template_path, output_dir)
                fusion_url_pairs.append([fusion, blurb_url])
            except ValueError as e:
                self.logger.error(f"Error processing fusion {fusion}: {e}")

        # Save the fusion-URL pairs to a CSV file
        output_csv_path = os.path.join(output_dir, 'fusion_blob_urls.csv')
        with open(output_csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Fusion', 'Whizbam URL'])
            writer.writerows(fusion_url_pairs)

        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS] = results
        data[core_constants.MERGE_INPUTS]['gene_information_merger'] = gene_info
        data[core_constants.MERGE_INPUTS]['treatment_options_merger'] = treatment_opts
        return data

    def process_fusion(self, fusion, tsv_file_path, json_template_path, output_dir):
        match = re.match(r"(.+)::(.+)", fusion)
        if match:
            gene1 = match.group(1)
            gene2 = match.group(2)
        else:
            raise ValueError(f"No valid fusion found for {fusion}.")

        breakpoint1, breakpoint2 = None, None

        with open(tsv_file_path, mode='r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                if row['gene1'] == gene1 and row['gene2'] == gene2:
                    breakpoint1 = row['breakpoint1']
                    breakpoint2 = row['breakpoint2']
                    break

        if not (breakpoint1 and breakpoint2):
            raise ValueError(f"No matching fusion found in the TSV file for {fusion}.")

        with open(json_template_path, 'r') as json_file:
            data = json.load(json_file)

        data['locus'] = [breakpoint1, breakpoint2]

        json_str = json.dumps(data, separators=(',', ':'))

        # Binary compressed data stream
        compressed_data = pysam.bgzip_compress(json_str.encode('utf-8'))
        # Take binary compressed data and encodes it into a base64 string
        base64_encoded = base64.b64encode(compressed_data).decode('utf-8')

        blurb_url = f"https://whizbam-dev.gsi.oicr.on.ca/igv?sessionURL=blob:{base64_encoded}"

        output_json_filename = f"{fusion}_details.json"
        output_json_path = os.path.join(output_dir, output_json_filename)
        with open(output_json_path, 'w') as output_json_file:
            json.dump(data, output_json_file, indent=2)

        return fusion, blurb_url

    def specify_params(self):
        discovered = [
            fc.MAVIS_PATH,
            fc.ARRIBA_PATH,
            core_constants.TUMOUR_ID,
            fc.ONCOTREE_CODE
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        # set defaults
        data_dir = directory_finder(self.log_level, self.log_path).get_data_dir()
        self.set_ini_default(fc.ENTREZ_CONVERSION_PATH, os.path.join(data_dir, fc.ENTRCON_NAME))
        self.set_ini_default(fc.MIN_FUSION_READS, 20)
        self.set_ini_default(oncokb.APPLY_CACHE, False)
        self.set_ini_default(oncokb.UPDATE_CACHE, False)
        self.set_ini_default(oncokb.ONCOKB_CACHE, self.CACHE_DEFAULT)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(fc.MAKO_TEMPLATE_NAME, data)

    def update_file_if_null(self, wrapper, ini_name, path_info_workflow_name):
        if wrapper.my_param_is_null(ini_name):
            self.logger.debug("Updating {0} with path info for {1}".format(ini_name, path_info_workflow_name))
            path_info = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
            file_path = path_info.get(path_info_workflow_name)
            if file_path == None:
                msg = "Cannot find {0} path for fusion input".format(path_info_workflow_name)
                self.logger.error(msg)
                raise RuntimeError(msg)
            wrapper.set_my_param(ini_name, file_path)
        return (wrapper)
