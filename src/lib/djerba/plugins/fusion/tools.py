"""
Utility classes for the fusions plugin
"""

import csv
import logging
import os
import re
import zlib
import base64
import json
import pandas as pd
from djerba.util.logger import logger
from djerba.util.oncokb.tools import levels as oncokb_levels
import djerba.util.oncokb.constants as oncokb
from djerba.util.html import html_builder as hb
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.util.oncokb.annotator import annotator_factory
from djerba.plugins.wgts.common.tools import wgts_tools
from djerba.util.oncokb.tools import gene_summary_reader
import djerba.plugins.fusion.constants as fc
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner

class fusion_tools(logger):

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        super().__init__()
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir
        self.df_fusions = self.get_fusions_df()
        self.df_fusions_indexed = self.df_fusions.copy().set_index('fusion_pairs')
        self.df_oncokb = self.get_oncokb_annotated_df()
        self.df_nccn = self.get_nccn_df()


    def assemble_data(self, oncotree_code):
        """
        Assemble the results for plugin.py/extract 
        Also returns gene info and treatment options 
        For every oncogenic entry in oncokb df, get the information from fusions df
        """
        
        def sort_by_actionable_level(row):
            return oncokb_levels.oncokb_order(row[core_constants.ONCOKB]) 

        results = {}
        results[fc.CLINICALLY_RELEVANT_VARIANTS] = len(self.df_oncokb)
        self.clinically_relevant_variants = len(self.df_oncokb) # value used by self.get_fusion_objects()
        results[fc.NCCN_RELEVANT_VARIANTS] = self.get_nccn_variants()
        self.nccn_relevant_variants = len(self.df_nccn) # value used by self.get_fusion_objects()
        results[fc.TOTAL_VARIANTS] = self.get_total_variants()

        # Get all fusions
        fusions = self.get_fusion_objects()

        # If there are fusions...
        if len(fusions) > 0:
            outputs = self.fusions_to_json(fusions, oncotree_code)
            [rows, gene_info, treatment_opts] = outputs

            # Sort by OncoKB level
            rows = sorted(rows, key=sort_by_actionable_level)
            rows = oncokb_levels.filter_reportable(rows)
            unique_rows = set(map(lambda x: x['fusion'], rows))

            results[fc.BODY] = rows
        else:
            results[fc.BODY] = []
            gene_info = []
            treatment_opts = []

        return results, gene_info, treatment_opts 

    def construct_whizbam_links(self, tsv_file_path, base_dir, fusion_dir, output_dir, json_template_path, unique_fusions, config, wrapper):

        failed_fusions = 0
        fusion_url_pairs = []

        for fusion in unique_fusions:
            try:
                fusion, blurb_url = self.process_fusion(config, fusion, tsv_file_path, json_template_path, output_dir, wrapper)
                fusion_url_pairs.append([fusion, blurb_url])

            except FusionProcessingError as e:
                self.logger.warning(f"Skipping fusion {fusion}: {e}")
                failed_fusions += 1

        if failed_fusions > 0:
            self.logger.warning(f"{failed_fusions} fusions failed out of {len(unique_fusions)}.")

        # Save the fusion-URL pairs to a CSV file
        output_tsv_path = os.path.join(output_dir, 'fusion_blurb_urls.tsv')
        with open(output_tsv_path, 'w', newline='') as tsvfile:
            writer = csv.writer(tsvfile, delimiter='\t')
            writer.writerow(['Fusion', 'Whizbam URL'])
            writer.writerows(fusion_url_pairs)

    def get_oncokb_annotated_df(self):
        """
        Get the oncokb df and turn it into a dataframe
        Only return those for which the mutation effect is not Unknown
        """
        df = pd.read_csv(os.path.join(self.work_dir, fc.DATA_FUSIONS_ANNOTATED), sep = "\t")
        if len(df) > 0:
            df = df[df.MUTATION_EFFECT != "Unknown"]
        return df

    def get_fusions_df(self):
        """
        Get the fusions df and turn it into a dataframe
        """
        df = pd.read_csv(os.path.join(self.work_dir, fc.DATA_FUSIONS), sep = "\t")
        return df

    def get_nccn_df(self):
        """
        Get the NCCN df and turn it into a dataframe
        """
        df = pd.read_csv(os.path.join(self.work_dir, fc.DATA_FUSIONS_NCCN), sep = "\t")
        df = df[~df["Fusion"].str.contains("None")]
        return df

    def get_total_variants(self):
        """
        Counts the number of UNIQUE genes in the fusions.
        Excludes Nones.
        Ex:
            NEMF-None
            DAZAP1-SBNO2
            MALRD1-MLLT10 
            KLK6-LDHB
            None-SLC25A3
            ANO1-None
            None-SBNO2
        This list should return a total of 9. 
        
        Code explanation:
            Gets a list of fusions by breaking up the separator -
            Some genes are hyphenated (ex. Gene1-Gene2-alpha is actually Gene1::Gene2-alpha).
            We should only split on the first hyphen. 
            Split will do 'KRAS-FGFR2' --> ['KRAS', 'FGFR2']
            Then, df.explode will make 'KRAS' and 'FGFR2' into two new rows for easy counting
        """
        # Get a unique list of fusions
        fusions = self.df_fusions['fusion_pairs'].str.split("-", n=1).explode('fusion_pairs')
        unique_fusions = list(set(fusions.to_list()))
        
        # We don't want to count Nones
        if "None" in unique_fusions:
            unique_fusions.remove("None")
        
        # Get total variants
        total_variants = len(unique_fusions)
        return total_variants


    def get_nccn_variants(self):
        """
        Counts the number of fusion PAIRS as NCCN number is reported as a pair.
        Deduplication was done in preprocess.py
        """
        # Get nccn variants
        nccn_variants = len(self.df_nccn)
        return nccn_variants

    def get_fusion_objects(self):
        """
        """

        def get_fusion_object(row, nccn=False):
            """
            If nccn = True, use prognostic level.
            """

            fusion_id_hyphen = row["Fusion"]
            #gene1 = fusion_id_hyphen.split("-", 1)[0]
            #gene2 = fusion_id_hyphen.split("-", 1)[1]
            #fusion_id = "::".join([gene1, gene2])
            
            fusion_id = self.df_fusions_indexed.loc[fusion_id_hyphen, "fusion_pairs_reordered"]
            gene1 = fusion_id.split("::", 1)[0]
            gene2 = fusion_id.split("::", 1)[1]

            reading_frame = self.df_fusions_indexed.loc[fusion_id_hyphen, "reading_frame_simple"]
            event_type = self.df_fusions_indexed.loc[fusion_id_hyphen, "event_type_simple"]
            
            if nccn == True:
                effect = "Undetermined"
                level = "P"
                therapies = {"P": "Prognostic"}
            else:
                level = oncokb_levels.parse_oncokb_level(row)
                therapies = oncokb_levels.parse_actionable_therapies(row)
                effect = row['MUTATION_EFFECT']

            fusion_object = fusion(
                    fusion_id,
                    gene1,
                    gene2,
                    reading_frame,
                    effect,
                    event_type,
                    level,
                    therapies
            )

            return fusion_object


        fusions = [] # Full list of all fusion results
        if self.clinically_relevant_variants != 0:
            for row in self.df_oncokb.iterrows():
                fusion_object = get_fusion_object(row[1].fillna(""))
                fusions.append(fusion_object)
        if self.nccn_relevant_variants != 0:
            for row in self.df_nccn.iterrows():
                fusion_object = get_fusion_object(row[1].fillna(""), nccn=True)
                fusions.append(fusion_object)

        # Sort them
        fusions = sorted(fusions, key=lambda f: f.get_fusion_id())

        return fusions


    def build_treatment_entries(self, fusion, therapies, oncotree_code):
        """Make an entry for the treatment options merger"""
        # TODO fix the treatment options merger to display 2 genes for fusions
        genes = fusion.get_genes()
        gene = genes[0]
        factory = tom_factory(self.log_level, self.log_path)
        entries = []
        for level in therapies.keys():
            entry = factory.get_json(
                tier=oncokb_levels.tier(level),
                level=level,
                treatments=therapies[level],
                gene=gene,
                alteration='Fusion',
                alteration_url=hb.build_fusion_url(genes, oncotree_code.lower())
            )
            entries.append(entry)
        return entries
    
    def build_treatment_entries_nccn(self, fusion, therapies, oncotree_code):
        """Make an entry for the treatment options merger, for NCCN biomarkers"""
        factory = tom_factory(self.log_level, self.log_path)
        entries = []
        for level in therapies.keys():
            entry = factory.get_json(
                tier=oncokb_levels.tier(level),
                level=level,
                treatments=therapies[level],
                gene=fusion.get_event_type(),
                alteration='Fusions and structural variants',
                #TODO: pull URL from NCCN_annotation.txt
                alteration_url="https://www.nccn.org/professionals/physician_gls/pdf/myeloma_blocks.pdf"
            )
            entries.append(entry)
        return entries


    def fusions_to_json(self, gene_pair_fusions, oncotree_code):
        rows = []
        gene_info = []
        treatment_opts = []
        cytobands = wgts_tools(self.log_level, self.log_path).cytoband_lookup()
        summaries = gene_summary_reader(self.log_level, self.log_path)
        gene_info_factory = gim_factory(self.log_level, self.log_path)
        # table has 2 rows for each oncogenic fusion
        # retain fusions with sort order less than (ie. ahead of) 'Likely Oncogenic'
        maximum_order = oncokb_levels.oncokb_order('P')
        for fusion in gene_pair_fusions:
            oncokb_order = oncokb_levels.oncokb_order(fusion.get_oncokb_level())
            if oncokb_order <= maximum_order:
                for gene in fusion.get_genes():
                    chromosome = cytobands.get(gene)
                    gene_url = hb.build_gene_url(gene)
                    row =  {
                        fc.GENE: gene,
                        fc.GENE_URL: gene_url,
                        fc.CHROMOSOME: chromosome,
                        fc.ONCOKB_LINK: fusion.get_oncokb_link(oncotree_code),
                        fc.FRAME: fusion.get_reading_frame(),
                        fc.TRANSLOCATION: fusion.get_event_type(),
                        fc.FUSION: fusion.get_fusion_id(),
                        fc.MUTATION_EFFECT: fusion.get_mutation_effect(),
                        core_constants.ONCOKB: fusion.get_oncokb_level()
                    }
                    rows.append(row)
                    gene_info_entry = gene_info_factory.get_json(
                        gene=gene,
                        summary=summaries.get(gene)
                    )
                    gene_info.append(gene_info_entry)
                therapies = fusion.get_therapies()
                if oncokb_order != oncokb_levels.oncokb_order('P'):
                    treatment_opts = self.build_treatment_entries(
                            fusion, 
                            therapies, 
                            oncotree_code
                    )
                else:
                    treatment_opts = self.build_treatment_entries_nccn(
                            fusion,
                            therapies,
                            oncotree_code
                    )

        return rows, gene_info, treatment_opts
    
    def process_fusion(self, config, fusion, tsv_file_path, json_template_path, output_dir, wrapper):

        # Validate and parse the fusion format
        match = re.match(r"(.+)::(.+)", fusion)
        if not match:
            msg = f"No valid fusion found for {fusion}. Ensure the format is gene1::gene2."
            self.logger.error(msg)
            raise FusionProcessingError(msg)
        gene1, gene2 = match.groups()

        # Find breakpoints in the ARRIBA TSV file
        breakpoint1, breakpoint2 = self.find_breakpoints(tsv_file_path, gene1, gene2)
        if not (breakpoint1 and breakpoint2):
            msg = f"No matching fusion found in the TSV file ({tsv_file_path}) for {fusion}."
            self.logger.error(msg)
            raise FusionProcessingError(msg)

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
        whizbam_project_id = wrapper.get_my_string(fc.WHIZBAM_PROJECT)
        data['tracks'][1]['name'] = tumour_id

        # Define file patterns
        bam_project_path = f"{core_constants.WHIZBAM_PATTERN_ROOT}/{project_id}/RNASEQ/{tumour_id}.bam"
        bai_project_path = f"{core_constants.WHIZBAM_PATTERN_ROOT}/{project_id}/RNASEQ/{tumour_id}.bai"
        bam_whizbam_path = f"{core_constants.WHIZBAM_PATTERN_ROOT}/{whizbam_project_id}/RNASEQ/{tumour_id}.bam"
        bai_whizbam_path = f"{core_constants.WHIZBAM_PATTERN_ROOT}/{whizbam_project_id}/RNASEQ/{tumour_id}.bai"

        # Resolve BAM file
        bam_file, bam_project = None, None
        if os.path.isfile(bam_project_path):
            bam_file, bam_project = bam_project_path, project_id
        elif os.path.isfile(bam_whizbam_path):
            bam_file, bam_project = bam_whizbam_path, whizbam_project_id
        else:
            self.logger.warning(f"BAM file not found for {project_id}. Try adjusting whizbam_project_id in config file")

        if bam_file:
            bam_filename = os.path.basename(bam_file)
            data['tracks'][1]['url'] = f"/bams/project/{bam_project}/RNASEQ/file/{bam_filename}"

        # Resolve BAI file
        bai_file, bai_project = None, None
        if os.path.isfile(bai_project_path):
            bai_file, bai_project = bai_project_path, project_id
        elif os.path.isfile(bai_whizbam_path):
            bai_file, bai_project = bai_whizbam_path, whizbam_project_id
        else:
            self.logger.warning(f"BAI file not found for {project_id}. Try adjusting whizbam_project_id in config file")

        if bai_file:
            bai_filename = os.path.basename(bai_file)
            data['tracks'][1]['indexURL'] = f"/bams/project/{bai_project}/RNASEQ/file/{bai_filename}"

        # Write the modified JSON to the output directory
        output_json_path = os.path.join(output_dir, f"{fusion}.json")
        with open(output_json_path, 'w') as json_output_file:
            json.dump(data, json_output_file)

        # Compress JSON and generate blurb URL
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


class fusion:
    # container for data relevant to reporting a fusion
    def __init__(
            self,
            fusion_id,
            gene1,
            gene2,
            reading_frame,
            effect,
            event_type,
            level,
            therapies,
    ):
        self.fusion_id = fusion_id
        self.gene1 = gene1
        self.gene2 = gene2
        self.reading_frame = reading_frame
        self.event_type = event_type
        self.effect = effect
        self.therapies = therapies
        self.level = level

    def get_fusion_id(self):
        return self.fusion_id

    def get_genes(self):
        return [self.gene1, self.gene2]

    def get_event_type(self):
        return self.event_type

    def get_reading_frame(self):
        return self.reading_frame

    def get_oncokb_link(self, oncotree):
        #need to both make the URL and then make the HTML for the URL
        gene1_url = hb.build_onefusion_url(self.gene1, oncotree)
        gene1_and_url = hb.href(gene1_url, self.gene1)
        gene2_url = hb.build_onefusion_url(self.gene2, oncotree)
        gene2_and_url = hb.href(gene2_url, self.gene2)
        return("::".join((gene1_and_url, gene2_and_url)))

    def get_oncokb_level(self):
        return self.level

    def get_mutation_effect(self):
        return self.effect

    def get_fda_level(self):
        return self.fda_level

    def get_therapies(self):
        return self.therapies

class FusionProcessingError(Exception):
    pass
