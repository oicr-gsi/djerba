"""
Fusion pre-processing of mavis and arriba files, as well as annotation.
Replaces legacy R script: fusions.R
"""

import csv
import logging
import os
import re
import pandas as pd
import numpy as np
from djerba.util.logger import logger
from djerba.util.environment import directory_finder
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.oncokb.annotator import annotator_factory
import djerba.plugins.fusion.constants as fc
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
pd.set_option('future.no_silent_downcasting', True)

class prepare_fusions(logger):

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        super().__init__()
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir
        self.data_dir = directory_finder(log_level, log_path).get_data_dir()

    def annotate_fusion_files(self, config_wrapper):
        # annotate from OncoKB
        # TODO check if fusions are non empty
        factory = annotator_factory(self.log_level, self.log_path)
        factory.get_annotator(self.work_dir, config_wrapper).annotate_fusion()

    def process_fusion_files(self, config_wrapper): 
        """
        MAIN FUNCTION, called by Extract.
        
        Inputs:
        - mavis file
        - arriba file
        - tumour id
        - oncotree code

        Outputs:
        - main fusions file with mavis and arriba information
        - annotated oncokb file
        """
        mavis_path = config_wrapper.get_my_string(fc.MAVIS_PATH)
        if not mavis_path: 
            msg = "Could not find mavis file. Perhaps you need to manually specify it?"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        arriba_path = config_wrapper.get_my_string(fc.ARRIBA_PATH)
        if not mavis_path:
            msg = "Could not find arriba file. Perhaps you need to manually specify it?"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        tumour_id = config_wrapper.get_my_string(core_constants.TUMOUR_ID)
        oncotree_code = config_wrapper.get_my_string(fc.ONCOTREE_CODE)
        oncotree_code = oncotree_code.upper()
        min_reads = config_wrapper.get_my_int(fc.MIN_FUSION_READS)
        
        self.logger.info("Processing fusion (mavis and arriba) results and writing fusion files")
        df_mavis = self.process_mavis(mavis_path, tumour_id, min_reads)
        df_arriba = self.process_arriba(arriba_path)
        self.write_fusion_files(df_mavis, df_arriba, oncotree_code)
        self.annotate_fusion_files(config_wrapper)
        self.logger.info("Finished writing fusion files")

    def add_dna_rna_support(self, df):
        """
        We want columns that looks like:
         
        DNA_support    RNA_support
        yes            yes
        no             yes
        yes            no
    
        If the tool used is delly, DNA_support = yes, otherwise DNA_support = no
        If the tool used is arriba OR star: RNA_support = yes, otherwise RNA_support = no
        """
      
        DNA_tools = df["tools"].str.contains("delly")
        RNA_tools = df["tools"].str.contains("star|arriba")
    
        df["DNA_support"] = np.select([DNA_tools], ["yes"], default = "no") 
        df["RNA_support"] = np.select([RNA_tools], ["yes"], default = "no") 
    
        return df

    def add_filter_sortby_read_support(self, df, min_reads):
        """
        There are multiple columns with read support. Which columns to use?
        The column called "call_method" tells us which read support column to choose.
        If the method is "contig" --> use the number under "contig_mapped reads"
        If the method is "flanking reads" --> use the number under "flanking reads"
        If the method is "split reads" --> use a combination of "break1_split_reads", 
                                          "break2_split_reads", and "linking_split_reads"
        If the method is a combination of methods (ex. "config;split reads"), read counts between methods will be summed.
        """

        def filter_and_sortby_read_support(df, min_reads):
            """
            Filters those entries for which read support is less than 20.
            Returns a sorted dfframe
            """
            df = df[df["read_support"] > min_reads] # > min_reads (as opposed to >= min_reads) was taken from legacy code. 
            df = df.sort_values(by=["read_support"], ascending=False)
            return df
        

        # Initialize read_support to 0 so we can sum read support methods if needed
        df["read_support"] = 0

        # Add values by call method
        df.loc[df["call_method"].str.contains("contig", na=False), "read_support"] += df["contig_remapped_reads"]
        df.loc[df["call_method"].str.contains("flanking reads", na=False), "read_support"] += df["flanking_pairs"]
        df.loc[df["call_method"].str.contains("split reads", na=False), "read_support"] += (
            df["break1_split_reads"] + df["break2_split_reads"] + df["linking_split_reads"]
        )

        df = filter_and_sortby_read_support(df, min_reads)

        return df
      
    def add_translocation_notation(self, df):
        """
        We want a column that looks like:
         
        translocation
        ---
        None
        t(12;14)
        None
        t(15;18)
        t(14;X)
        None
        None
        
        The translocation notation will be present for those which the event-type
        is translocation or inverted translocation.
        """
        
        translocation_cases = df["event_type"].isin(["translocation", "inverted translocation"])
        
        event_types = [
            translocation_cases,  
            ~translocation_cases  # Everything else. "~" is like "not()" but on a series 
        ]
        
        new_entry = [
            "t(" + df["break1_chromosome"].astype(str) + ";" + df["break2_chromosome"].astype(str) + ")",  
            "None"
        ]
        
        df["translocation"] = np.select(event_types, new_entry, default = 0) # Defaults to 0 if something else
        
        # Correct the translocation notation
        df = self.correct_translocation_notation(df)
        
        return df
    
    def add_tumour_id(self, df, tumour_id):
        """
        Adds a column with the tumour id
        """
        df["Sample"] = tumour_id
        return df

    def change_column_name(self, df, old_column, new_column):
        """
        Changes column name from old_column to new_column
        """
        df.rename(columns={old_column: new_column}, inplace=True)
        return df
      
    def correct_translocation_notation(self, df):
        """
        Translocations should be in t(min_chrom;max_chrom) notation with X always on the right
        Thank you ChatGPT for the regex
        """
    
        def format_translocation(entry):
    
            if not isinstance(entry, str) or not entry.startswith("t("):
                return "None"  # change to "None" if it's not a translocation entry
            
            # extract chromosome names
            entry = entry.replace("{", "(").replace("}", ")").replace(",", ";")
            match = re.match(r"t\((\w+);(\w+)\)", entry)
    
            if match:
                chrom1, chrom2 = match.groups()
                
                if chrom1 == "X" or chrom2 == "X":
                    return f"t({min(chrom1, chrom2)};X)" 
                elif chrom1 == "Y" or chrom2 == "Y":
                    return f"t({min(chrom1, chrom2)};Y)"
                else:
                    chrom1_num = int(chrom1)
                    chrom2_num = int(chrom2)
                    return f"t({min(chrom1_num, chrom2_num)};{max(chrom1_num, chrom2_num)})"

            return entry  
    
        df["translocation"] = df["translocation"].apply(format_translocation)
        return df 
      
    def delete_delly_only_calls(self, df):
        """
        The old version of the fusion plugin also removed delly-only calls.
        Supposedly because delly = structural variants and they weren't validated.
        """
        df = df[df.tools != "delly"]   
        return df

    def df_for_oncokb_annotator(self, df):
        """
        Makes the dataframe that will be ready for input into the oncokb annotator.
        The annotator only requires two columns:
            1. Tumor_Sample_Barcode	(ex. OCT2-01-0014-ARC_SE24-0335)
            2. Fusion (ex. KRAS-FGFR2)
        It is deduplicated further as the oncokb annotator does not care about event types.
        We also remove any fusion pairs with None as they will not be reported in Djerba.
        """
        new_df = df[["Sample", "fusion_pairs"]].copy()
        new_df = self.drop_duplicates(new_df, ["fusion_pairs"])
        new_df["fusion_pairs"] = new_df["fusion_pairs"].astype(str)
        new_df = new_df[~new_df["fusion_pairs"].str.contains("None")]
        # Change headers
        new_df.rename(columns={'Sample': 'Tumor_Sample_Barcode', 'fusion_pairs': 'Fusion'}, inplace=True)

        return new_df
      
    def drop_duplicates(self, df, columns):
        """
        """
        df = df.drop_duplicates(subset=columns)
        return df
        
    def drop_duplicates_merge_columns(self, df):
        """
        """
    
        columns = df.groupby("fusion_pairs", as_index=False).agg({
            "event_type": lambda x: ";".join(x.unique()),
            "reading_frame": lambda x: ";".join(x.dropna().astype(str).unique())
        })
        df = df.drop(columns=["event_type", "reading_frame"]).merge(columns, on="fusion_pairs")
        df = self.drop_duplicates(df, "fusion_pairs")
        return df
    
    def left_join(self, df1, df2, column):
        """
        Performs a left join of df2 into df1 on a column.
        Assumes fusions are sorted alphabetically (as is done in write_fusion_pairs) 
        If a row in df1 matches multiple rows in df2, then df1 will duplicate that row for every match in df2.
        
        INPUTS
        df_dedup
        fusion_pairs	Other_col1
        A-B	            X1
        D-F	            X2
        Q-R	            X3
        
        arriba
        fusion_pairs	Extra_info
        A-B	            Y1
        D-E	            Y2
        D-F	            Y3
        D-F                 Y4
        
        OUTPUT
        fusion_pairs	Other_col1	Extra_info
        A-B	            X1	        Y1
        D-F	            X2	        Y3
        D-F                 X2          Y4
        Q-R	            X3	        NaN
        """
        df1 = df1.merge(df2, on=column, how="left")
        return df1
        
    def merge_mavis_arriba(self, df_mavis, df_arriba):
        """
        This function merges mavis and arriba information and does some additional processing
        This is for CGI to be able to review mavis and arriba information for called fusions.
        Processing includes replacing unknown reading frames, removing duplicates, merging columns, etc.

        """

        # Merge df_arriba information into df_mavis
        df_merged = self.left_join(df_mavis, df_arriba, "fusion_pairs")
        # Remove duplicate fusions (but keep if they are different event types)
        df_merged = self.drop_duplicates_merge_columns(df_merged)
        # Remove fusions that are self-self pairs
        df_merged = self.remove_self_fusions(df_merged)
        # All nan reading frame columns should be Unknown
        # If reading frame is anything except in-frame, out-of-frame, or stop-codon, make it nan
        df_merged = self.simplify_reading_frame(df_merged)
        # Simplify event type
        df_merged = self.simplify_event_type(df_merged)
        # Re-order fusions to be in 5'::3' order.
        df_merged = self.reorder_fusions(df_merged)
        # Delete all delly-only calls
        # NOTE: this is supposedly because structural variants were not validated.
        # NOTE: the old version of the fusion plugin also excluded delly-only calls.
        df_merged = self.delete_delly_only_calls(df_merged)

        return df_merged
        
    def process_arriba(self, arriba_path):
        """
        Process arriba information via pandas dataframe operations.
        Processing includes changing column names and writing fusion pairs for merging with mavis.
        Returns a processed arriba dataframe.
        """
        # Get the data_frame if the arriba path is not completely empty:
        # Note: the code should work even if there is only a header.
        if os.path.getsize(arriba_path) != 0:
            df_arriba = pd.read_csv(arriba_path, sep = '\t')
            # First two columns are called "#gene1" and "gene2". Rename first to "gene1" for convenience.
            df_arriba = self.change_column_name(df_arriba, "#gene1", "gene1")    
            # Add fusion tuples as well, for merging with mavis
            df_arriba = self.write_fusion_pairs(df_arriba, "gene1", "gene2")
        else:
            msg = "Arriba file is completely empty (no header)."
            self.logger.info(msg)
            df_arriba = pd.DataFrame()

        return df_arriba

    def process_mavis(self, mavis_path, tumour_id, min_reads):
        """
        Process mavis information via pandas dataframe operations.
        Processing includes fixing column formats, filtering by read support, adding translocation notation, etc.
        Returns a processed mavis dataframe.
        """
        # Get the data_frame if the mavis path is not completely empty:
        # Note: the code should work even if there is only a header 
        if os.path.getsize(mavis_path) != 0:
            df_mavis = pd.read_csv(mavis_path, sep = '\t')
            # Add a column with tumour id
            df_mavis = self.add_tumour_id(df_mavis, tumour_id)
            # Preprocess the columns containing read information (Nones to 0, semi-colon entries, strings to floats, etc.)
            df_mavis = self.split_column_take_max(df_mavis)
            # Add a column with read support based on the call method
            df_mavis = self.add_filter_sortby_read_support(df_mavis, min_reads)
            # Add a column describing translocations if it's a translocation event (i.e. t(x;y) notation)
            # Otherwise use None
            df_mavis = self.add_translocation_notation(df_mavis)
            # Add DNA_suppot and RNA_support columns
            df_mavis = self.add_dna_rna_support(df_mavis) 
            # Add a column with fusion pairs
            df_mavis = self.write_fusion_pairs(df_mavis, "gene1_aliases", "gene2_aliases")
        else:
            msg = "Mavis file is completely empty (no header)."
            self.logger.info(msg)
            df_mavis = pd.DataFrame()
        
        return df_mavis
        
    def process_nccn(self, df_merged, oncotree_code):
        """
        Looks only at the NCCN translocations in djerba/data/NCCN_annotations.txt
        Makes the nccn dataframe that will be ready for input into the oncokb annotator.
        The annotator only requires two columns:
            1. Tumor_Sample_Barcode     (ex. OCT2-01-0014-ARC_SE24-0335)
            2. Fusion (ex. KRAS-FGFR2)
        It is deduplicated further as the oncokb annotator does not care about event types.
        We also remove any fusion pairs with None as they will not be reported in Djerba.
        """

        df_annotations = pd.read_csv(os.path.join(self.data_dir, fc.NCCN_ANNOTATION_FILE), sep = '\t')
        
        marker_dict = dict(zip(df_annotations["marker"], df_annotations["oncotree"]))

        dict_nccn = {"Tumor_Sample_Barcode":[], "Fusion": []}
        for row in df_merged.iterrows():
            translocation = row[1]["translocation"]
            if translocation in marker_dict and oncotree_code == marker_dict[translocation]:
                dict_nccn["Fusion"].append(row[1]["fusion_pairs"])
                dict_nccn["Tumor_Sample_Barcode"].append(row[1]["Sample"])

        df_nccn = pd.DataFrame(dict_nccn)
        return df_nccn
        
    def remove_self_fusions(self, df):
        """
        Removes fusions of the nature Fusion1-Fusion1
        ex. CDKN2A-CDKN2A
        """
        df = df[~df["fusion_pairs"].apply(
            lambda x: x.split("-")[0] == x.split("-")[1]
            )
        ]
        return df

    def reorder_fusions(self, df):
        """
        Fusions must be in the order ${5_Prime_Fusion}::${3_Prime_Fusion}
        Mavis contains information about which gene is 5' and which is 3'
        but Mavis is not consistent with the order.
        Re-order fusions so it's always 5' first.
        Don't care how reordering impacts Nones; these get filtered out later anyways
        """
        # Make fusion_pairs but ensure 5' always comes first
        df["fusion_pairs_reordered"] = np.where(
            df["gene1_direction"] > df["gene2_direction"], # 5 > 3
            df["gene1_aliases"] + "::" + df["gene2_aliases"], # Write 5'::3' gene
            df["gene2_aliases"] + "::" + df["gene1_aliases"] # Write 3'::5' gene
        )
        return df

    def simplify_event_type(self, df):
        """
        Changes multiple event types to "Undetermined".
        Changes any event type with "translocation" to the actual translocation event.
        Changes any event type with "inversion" to the actual inversion event.
        """

        # New column that simplifies entries that have multiple event types (ex. "inversion;duplication") with just "Undetermined"
        df["event_type_simple"] = np.where(
            df["event_type"].str.contains(";"), "Undetermined", df["event_type"]
        )

        # Replace "translocation" with the corresponding translocation entry
        df["event_type_simple"] = np.where(
            df["event_type"].str.contains("translocation"),
            df["translocation"],
            df["event_type"]
        )

        # Replace "inversion" with the corresponding inversion
        df["event_type_simple"] = np.where(
            df["event_type"].str.contains("inversion"),
            "inv(" + df["break1_chromosome"].astype(str) + ")",
            df["event_type_simple"]
        )

        return df

    def simplify_reading_frame(self, df):
        """
        Replaces all nan reading frame with Unknown.
        Also adds a new column that simplifies entries that have multiple reading frames (ex. "in-frame;out-of-frame") with just "Mutliple Frames"
        Chose to keep it as a second column so the more informative column can be kept and reviewed by CGI if needed.
        Valid reading frames are in-frame, out-of-frame, and stop-codon.
        According to the arriba documentation:

            reading_frame : This column states whether the gene at the 3' end of the fusion is fused in-frame or out-of-frame.
            The value stop-codon indicates that there is a stop codon prior to the fusion junction, such that the 3' end is not translated,
            even if the reading frame is preserved across the junction. The prediction of the reading frame builds on the prediction of the
            peptide sequence. A dot (.) indicates that the peptide sequence cannot be predicted, for example, because the transcript sequence
            could not be determined or because the breakpoint of the 5' gene does not overlap a coding region

        Anything else should be left as nan.

        """
        
        df["reading_frame"] = df["reading_frame"].replace([".", ""], np.nan)
        df["reading_frame"] = df["reading_frame"].fillna("Unknown")

        # New column that simplifies entries that have multiple reading frames (ex. "in-frame;out-of-frame") with just "Mutliple Frames"
        df["reading_frame_simple"] = np.where(
            df["reading_frame"].str.contains(";"), "Multiple Frames", df["reading_frame"]
        )
        return df

    def split_column_take_max(self, df):
        """
        This split_column_take_max function is necessary because
        some columns look like this:
        
        config_remapped_reads
        5
        0
        18
        21;6
        None
        
        ^so out of those, we want to return something like
        
        config_remapped_reads
        5
        0
        18
        21
        0
        """
        columns = ["contig_remapped_reads", "flanking_pairs", "break1_split_reads", "break2_split_reads", "linking_split_reads"]
        for column in columns:
            df[column] = df[column].astype(str).apply(
              lambda x: int(max(
                [float(i) if i not in ["None", "nan"] else 0 for i in x.split(';')]  
            )))
        return df

    def write_fusion_files(self, df_mavis, df_arriba, oncotree_code):
        """
        Writes data_fusions.txt to the workspace.
        It also writes data_fusions_oncokb.txt to the workspace.
        This is for the oncokb annotator to use.
        It looks like:

        Sample          Fusion
        my_sample_id    ACTN1-DACH2
        my_sample_id    BROX-FGFR2
        my_sample_id    DENND2C-PKN2
        ...             ...

        This function does not return anything.
        """
        
        if df_mavis.empty:
            # I.e. if all above filtering steps leave no fusions
            # The usual culprit is that no fusions have greater than 20 reads

            df_merged = self.left_join(df_mavis, df_arriba, "fusion_pairs")

        else:
            df_merged = self.merge_mavis_arriba(df_mavis, df_arriba)

        # Get the NCCN calls
        df_nccn = self.process_nccn(df_merged, oncotree_code)

        # Make the dataframe for oncokb annotation
        df_oncokb = self.df_for_oncokb_annotator(df_merged)

        # Write data_fusions.txt to the workspace for main reporting task
        df_merged.to_csv(os.path.join(self.work_dir, fc.DATA_FUSIONS), index = False, sep = "\t")
        
        # Write data_fusions_oncokb.txt to the workspace for annotation task
        df_oncokb.to_csv(os.path.join(self.work_dir, fc.DATA_FUSIONS_ONCOKB), index = False, sep = "\t")

        df_nccn.to_csv(os.path.join(self.work_dir, fc.DATA_FUSIONS_NCCN), index = False, sep = "\t")

    def write_fusion_pairs(self, df, column1, column2):
        """
        Takes genes in gene1_aliases and gene2_aliases and concatonates with ::
        Ex. 
    
        gene1_aliases    gene2_aliases
        FGFR2            KRAS
        
        Will make a third column
        
        gene1_aliases    gene2_aliases      fusion_pairs
        FGFR2            KRAS               FGFR2-KRAS
        
        The new delimiter is ::, but - is used for now as OncoKB requires it.
        It always orders it alphabetically.
        """
        # First change all nans to the string None
        df[column1] = df[column1].replace({np.nan: None})
        df[column2] = df[column2].replace({np.nan: None})
    
        
        # Make fusion tuples 
        df["fusion_pairs"] = df.apply(lambda row: "-".join(sorted([str(row[column1]), str(row[column2])])), axis=1)
        return df 

class FileNotFoundError(Exception):
    pass
