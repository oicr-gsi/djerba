"""
Utility classes for the fusions plugin
"""

import csv
import logging
import os
import re
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

class fusion_reader(logger):

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        super().__init__()
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir
        self.df_fusions = self.get_fusions_df()
        self.df_fusions_indexed = self.df_fusions.copy().set_index('fusion_pairs')
        self.df_oncokb = self.get_oncokb_annotated_df()
        #annotations = self.read_annotation_data()


    def assemble_data(self, oncotree_code):
        """
        For every oncogenic entry in oncokb df, get the information from fusions df
        """
        def sort_by_actionable_level(row):
            return oncokb_levels.oncokb_order(row[core_constants.ONCOKB]) 

        results = {}
        results[fc.CLINICALLY_RELEVANT_VARIANTS] = len(self.df_oncokb)
        self.clinically_relevant_variants = len(self.df_oncokb)
        results[fc.TOTAL_VARIANTS] = self.get_total_variants()
        results[fc.NCCN_VARIANTS] = 0


        fusions = self.get_fusion_objects()
        if len(fusions) > 0:

            outputs = self.fusions_to_json(fusions, oncotree_code)
            [rows, gene_info, treatment_opts] = outputs

            # Sort by OncoKB level
            rows = sorted(rows, key=sort_by_actionable_level)
            rows = oncokb_levels.filter_reportable(rows)
            unique_rows = set(map(lambda x: x['fusion'], rows))

            results[fc.BODY] = rows
        
        else:
            results[fc.body] = 0
            gene_info = []
            treatment_opts = []

        return results

        #print(fusion_object.fusion_id)
        #print(fusion_object.gene1)
        #print(fusion_object.gene2)
        #print(fusion_object.reading_frame)
        #print(fusion_object.effect)
        #print(fusion_object.level)
        #print(fusion_object.therapies)
        #print(fusion_object.event_type)
    
    def get_oncokb_annotated_df(self):
        """
        Get the oncokb df and turn it into a dataframe
        Only return those for which the mutation effect is not Unknown
        """
        df = pd.read_csv(os.path.join(self.work_dir, fc.DATA_FUSIONS_ANNOTATED), sep = "\t")
        df = df[df.MUTATION_EFFECT != "Unknown"]
        return df

    def get_fusions_df(self):
        """
        Get the fusions df and turn it into a dataframe
        """
        df = pd.read_csv(os.path.join(self.work_dir, fc.DATA_FUSIONS), sep = "\t")
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


    def get_fusion_objects(self):
        """
        """

        def get_fusion_object(row):
            """
            """

            fusion_id_hyphen = row["Fusion"]
            gene1 = fusion_id_hyphen.split("-", 1)[0]
            gene2 = fusion_id_hyphen.split("-", 1)[1]
            fusion_id = "::".join([gene1, gene2])
            reading_frame = self.df_fusions_indexed.loc[fusion_id_hyphen, "reading_frame_simple"]
            event_type = self.df_fusions_indexed.loc[fusion_id_hyphen, "event_type"]
            level = oncokb_levels.parse_oncokb_level(row)
            therapies = oncokb_levels.parse_actionable_therapies(row)
            effect =  row['MUTATION_EFFECT']

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

        # Sort them
        fusions = sorted(fusions, key=lambda f: f.get_fusion_id())
        return fusions

    def get_fusion_object(self, row):
        """
        """
        
        fusion_id_hyphen = row["Fusion"]
        gene1 = fusion_id_hyphen.split("-", 1)[0]
        gene2 = fusion_id_hyphen.split("-", 1)[1]
        fusion_id = "::".join([gene1, gene2])
        reading_frame = self.df_fusions_indexed.loc[fusion_id_hyphen, "reading_frame_simple"]
        event_type = self.df_fusions_indexed.loc[fusion_id_hyphen, "event_type"]
        level = oncokb_levels.parse_oncokb_level(row)
        therapies = oncokb_levels.parse_actionable_therapies(row)
        effect =  row['MUTATION_EFFECT']  
        
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

    def _collate_row_data(self, fusion_data, annotations):
        fusions = []  # List to store valid fusion entries
        fusion_genes = set()  # Set to track distinct genes involved in fusions
        self.logger.debug("Starting to collate fusion table data.")
        intragenic = 0  # Counter for intragenic fusions
        nccn_fusion_total = 0  # Counter for fusions rescued by NCCN annotation
        NCCN_fusions = set()  # Set to store NCCN-annotated fusions

        # Read NCCN-annotated fusions from a file
        with open(os.path.join(self.input_dir, fc.DATA_FUSIONS_NCCN_ANNOTATED)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                NCCN_fusions.add(row['Fusion'])  # Add each fusion ID to the set

        # Iterate over all fusion IDs in fusion_data
        for fusion_id in fusion_data.keys():
            gene2_exists = True  # Assume a second gene exists initially
            # Case: Intragenic fusions (only one gene involved)
            if len(fusion_data[fusion_id]) == 1:
                # Skip intragenic fusions, but add to the gene count
                fusion_genes.add(fusion_data[fusion_id][0][fc.HUGO_SYMBOL])
                if fusion_id in NCCN_fusions:
                    # If the fusion is in the NCCN-annotated list, it's "rescued"
                    self.logger.debug("Fusion {0} rescued by NCCN annotation".format(fusion_id))
                    gene2_exists = False  # No second gene; marked as "Intergenic"
                    gene2 = "Intergenic"
                    nccn_fusion_total += 1  # Increment NCCN-rescued fusion count
                else:
                    intragenic += 1  # Increment intragenic count and skip processing
                    continue
            elif len(fusion_data[fusion_id]) >= 3:
                # Error case: More than two genes for a single fusion ID
                msg = "More than 2 fusions with the same name: {0}".format(fusion_id)
                self.logger.error(msg)
                raise RuntimeError(msg)

            # Normal case: Valid fusion data with one or two genes
            gene1 = fusion_data[fusion_id][0][fc.HUGO_SYMBOL]
            if gene2_exists:
                # If a second gene exists, retrieve it
                gene2 = fusion_data[fusion_id][1][fc.HUGO_SYMBOL]
                # Add both genes to the set
                fusion_genes.add(gene1)
                fusion_genes.add(gene2)

            # Case: Two genes exist for the fusion
            if gene2_exists:
                for row_input in annotations[fusion_id]:
                    effect = row_input['MUTATION_EFFECT']  # Get mutation effect
                level = oncokb_levels.parse_oncokb_level(row_input)  # Parse oncokb level
            else:
                # Case: No second gene (rescued by NCCN)
                effect = "Undetermined"
                level = "P"

            # If the level is valid, add therapies information
            if level not in ['Unknown', 'NA']:
                if gene2_exists:
                    therapies = oncokb_levels.parse_actionable_therapies(row_input)
                else:
                    therapies = {"P": "Prognostic"}
                # Append a new fusion object to the list
                fusions.append(
                    fusion(
                        fusion_id,
                        fusion_data[fusion_id][0]['Fusion_newStyle'],
                        gene1,
                        gene2,
                        fusion_data[fusion_id][0]['Frame'],
                        effect,
                        level,
                        therapies,
                        fusion_data[fusion_id][0]['translocation']
                    )
                )
        total = len(fusions) - nccn_fusion_total
        total_fusion_genes = len(fusion_genes)  # Count distinct genes

        msg = "Finished collating fusion table data. " + \
              "Found {0} fusion rows for {1} distinct genes; ".format(total, total_fusion_genes) + \
              "excluded {0} intragenic rows.".format(intragenic)
        self.logger.info(msg)

        for fusion_row in fusions:
            self.logger.debug("Fusions: {0}".format(fusion_row.get_genes()))

        return [fusions, total_fusion_genes, total, nccn_fusion_total]

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
                alteration='Fusion',
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
                    for level in therapies.keys():
                        if oncokb_order != oncokb_levels.oncokb_order('P'):
                            entries = self.build_treatment_entries(
                                fusion,
                                therapies,
                                oncotree_code.lower()
                            )
                            treatment_opts.extend(entries)
                        else:
                            entries = self.build_treatment_entries_nccn(
                                fusion,
                                therapies,
                                oncotree_code.lower()
                            )
                            treatment_opts.extend(entries)
        return rows, gene_info, treatment_opts
    
    def get_fusions(self):
        return self.fusions

    def get_total_nccn_fusions(self):
        return self.total_nccn_fusions






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





