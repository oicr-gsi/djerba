"""
Plugin to generate the Fusions report section
"""

import csv
import logging
import os
import re
import glob
import warnings
import json
import zlib
import base64
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.plugins.fusion.tools import fusion_reader, prepare_fusions
from djerba.util.environment import directory_finder
from djerba.util.logger import logger
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb
import djerba.plugins.fusion.constants as fc

class FusionProcessingError(Exception):
    pass

class main(plugin_base):
    PRIORITY = 900
    PLUGIN_VERSION = '1.1.0'
    CACHE_DEFAULT = '/.mounts/labs/CGI/gsi/tools/djerba/oncokb_cache/scratch'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper = self.update_file_if_null(wrapper, fc.ARRIBA_PATH, 'arriba')
        wrapper = self.update_file_if_null(wrapper, fc.MAVIS_PATH, 'mavis')
        wrapper = self.update_wrapper_if_null(wrapper, 'input_params.json', fc.WHIZBAM_PROJECT, 'whizbam_project')
        self.update_wrapper_if_null(wrapper, 'input_params.json', fc.ONCOTREE_CODE, 'oncotree_code')

        sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)

        if wrapper.my_param_is_null(core_constants.TUMOUR_ID):
            wrapper.set_my_param(core_constants.TUMOUR_ID, sample_info.get(core_constants.TUMOUR_ID))
        if wrapper.my_param_is_null(core_constants.PROJECT):
            wrapper.set_my_param(core_constants.PROJECT, sample_info.get(core_constants.PROJECT))

        return wrapper.get_config()

    def extract(self, config):
        def sort_by_actionable_level(row):
            return oncokb_levels.oncokb_order(row[core_constants.ONCOKB])

        wrapper = self.get_config_wrapper(config)
        whizbam_project_id = wrapper.get_my_string(fc.WHIZBAM_PROJECT)
        prepare_fusions(self.workspace.get_work_dir(), self.log_level, self.log_path).process_fusion_files(wrapper)
        fus_reader = fusion_reader(self.workspace.get_work_dir(), self.log_level, self.log_path)
        total_fusion_genes = fus_reader.get_total_fusion_genes()
        gene_pair_fusions = fus_reader.get_fusions()
        if gene_pair_fusions is not None:

            outputs = fus_reader.fusions_to_json(gene_pair_fusions, wrapper.get_my_string(fc.ONCOTREE_CODE))
            [rows, gene_info, treatment_opts] = outputs
            
            # Sort by OncoKB level
            rows = sorted(rows, key=sort_by_actionable_level)
            rows = oncokb_levels.filter_reportable(rows)
            unique_rows = set(map(lambda x: x['fusion'], rows))

            results = {
                fc.TOTAL_VARIANTS: total_fusion_genes,
                fc.CLINICALLY_RELEVANT_VARIANTS: len(unique_rows),
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
        base_dir = (directory_finder(self.log_level, self.log_path).get_base_dir())
        fusion_dir = os.path.join(base_dir, "plugins", "fusion")
        json_template_path = os.path.join(fusion_dir, fc.JSON_TO_BE_COMPRESSED)
        output_dir = self.workspace.get_work_dir()
        unique_fusions = list({item["fusion"] for item in results[fc.BODY]})
        fusion_url_pairs = []

        failed_fusions = 0

        for fusion in unique_fusions:
            try:
                fusion, blurb_url = self.process_fusion(config, fusion, tsv_file_path, json_template_path, output_dir, whizbam_project_id)
                fusion_url_pairs.append([fusion, blurb_url])

            except FusionProcessingError as e:
                self.logger.error(f"Skipping fusion {fusion}: {e}")
                failed_fusions += 1

        if failed_fusions > 0:
            self.logger.warning(f"{failed_fusions} fusions failed out of {len(unique_fusions)}.")

        # Save the fusion-URL pairs to a CSV file
        output_tsv_path = os.path.join(output_dir, 'fusion_blurb_urls.tsv')
        with open(output_tsv_path, 'w', newline='') as tsvfile:
            writer = csv.writer(tsvfile, delimiter='\t')
            writer.writerow(['Fusion', 'Whizbam URL'])
            writer.writerows(fusion_url_pairs)

        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS] = results
        data[core_constants.MERGE_INPUTS]['gene_information_merger'] = gene_info
        data[core_constants.MERGE_INPUTS]['treatment_options_merger'] = treatment_opts
        return data

    def process_fusion(self, config, fusion, tsv_file_path, json_template_path, output_dir, whizbam_project_id):
        wrapper = self.get_config_wrapper(config)

        # Validate and parse the fusion format
        match = re.match(r"(.+)::(.+)", fusion)
        if not match:
            raise FusionProcessingError(f"No valid fusion found for {fusion}. Ensure the format is gene1::gene2.")
        gene1, gene2 = match.groups()

        # Find breakpoints in the ARRIBA TSV file
        breakpoint1, breakpoint2 = self.find_breakpoints(tsv_file_path, gene1, gene2)
        if not (breakpoint1 and breakpoint2):
            raise FusionProcessingError(f"No matching fusion found in the TSV file ({tsv_file_path}) for {fusion}.")

        # Format breakpoints
        formatted_breakpoint1 = self.format_breakpoint(breakpoint1)
        formatted_breakpoint2 = self.format_breakpoint(breakpoint2)

        # Load the JSON template
        with open(json_template_path, 'r') as json_file:
            data = json.load(json_file)

        # Update the JSON with the formatted breakpoints
        data['locus'] = [formatted_breakpoint1, formatted_breakpoint2]

        project_id = wrapper.get_my_string(core_constants.PROJECT)
        tumour_id = wrapper.get_my_string(core_constants.TUMOUR_ID)
        data['tracks'][1]['name'] = tumour_id

        # Search for the BAM and BAI files using glob.glob
        bam_pattern = f"{core_constants.WHIZBAM_PATTERN_ROOT}/{project_id}/RNASEQ/{tumour_id}.bam"
        bai_pattern = f"{core_constants.WHIZBAM_PATTERN_ROOT}/{project_id}/RNASEQ/{tumour_id}.bai"

        bam_files = glob.glob(bam_pattern)
        bai_files = glob.glob(bai_pattern)

        # Fallback to whizbam_project_id if path doesn't exist
        if not bam_files:
            bam_pattern = f"{core_constants.WHIZBAM_PATTERN_ROOT}/{whizbam_project_id}/RNASEQ/{tumour_id}.bam"
            bam_files = glob.glob(bam_pattern)
        if not bai_files:
            bai_pattern = f"{core_constants.WHIZBAM_PATTERN_ROOT}/{whizbam_project_id}/RNASEQ/{tumour_id}.bai"
            bai_files = glob.glob(bai_pattern)

        # Handle BAM files
        if bam_files:
            bam_file = bam_files[0]
            filename = os.path.basename(bam_file)
            data['tracks'][1]['url'] = f"/bams/project/{project_id}/RNASEQ/file/{filename}"
        else:
            warnings.warn(f"BAM file not found for pattern: {bam_pattern}")

        # Handle BAI files
        if bai_files:
            bai_file = bai_files[0]
            filename = os.path.basename(bai_file)
            data['tracks'][1]['indexURL'] = f"/bams/project/{project_id}/RNASEQ/file/{filename}"
        else:
            warnings.warn(f"BAI file not found for pattern: {bai_pattern}")

        # Write the modified JSON to the output directory
        output_json_path = os.path.join(output_dir, f"{fusion}.json")
        with open(output_json_path, 'w') as json_output_file:
            json.dump(data, json_output_file)

        with open(output_json_path, 'r') as json_output_file:
            json_content = json_output_file.read()
        compressed_b64_data = self.compress_string(json_content)
        blurb_url = f"https://whizbam.oicr.on.ca/igv?sessionURL=blob:{compressed_b64_data}"
        return fusion, blurb_url

    def find_breakpoints(self, tsv_file_path, gene1, gene2):
        # Find breakpoints for the given fusion genes in the arriba file
        with open(tsv_file_path, mode='r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                if (row['#gene1'] == gene1 or row['#gene1'] == gene2) and (
                        row['gene2'] == gene1 or row['gene2'] == gene2):
                    return row['breakpoint1'], row['breakpoint2']
        return None, None

    def format_breakpoint(self, breakpoint):
        # Format breakpoint into 'chr:start-end' format
        chrom, pos = breakpoint.split(':')
        start = int(pos)
        return f"{chrom}:{start}-{start + 1}"

    def compress_string(self, input_string):
        # Convert string to bytes
        input_bytes = input_string.encode(core_constants.TEXT_ENCODING)
        # Compress using raw deflate (no zlib header)
        compressed_bytes = zlib.compress(input_bytes, level=9)[2:-4]  # Removing zlib headers and checksum
        # Encode compressed bytes to base64
        compressed_base64 = base64.b64encode(compressed_bytes)
        # Convert the base64 bytes to a string and apply the replacements
        return compressed_base64.decode(core_constants.TEXT_ENCODING)

    def specify_params(self):
        discovered = [
            core_constants.PROJECT,
            fc.MAVIS_PATH,
            fc.ARRIBA_PATH,
            core_constants.TUMOUR_ID,
            fc.ONCOTREE_CODE,
            fc.WHIZBAM_PROJECT
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
        return wrapper
