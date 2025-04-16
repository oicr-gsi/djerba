# Fusion Plugin

The fusion plugin identifies oncogenic fusions in tumour samples.

## Pipeline
Uses Delly/Mavis/Arriba/Starfusion

## Plugin Breakdown

The plugin is composed of the following files:
- **plugin.py**:
    - The main code
    - It calls configure, extract, and render methods to generate the fusions section
- **preprocess.py**:
    - Called by extract
    - Performs data wrangling on mavis and arriba fusion output
    - Annotates the fusions using the oncokb annotator
    - Outputs the following files to the workspace:
        - "data_fusions.txt"
        - "data_fusions_oncokb.txt"
        - "data_fusions_obcokb_annotated.txt"
        - "data_fusions_NCCN.txt"
- **tools.py**:
    - Called by extract
    - Uses output from preprocess.py to assemble all data for the fusions section
- **fusion_template.html**:
    - Called by render
    - Contains the template for rendering fusions in the clinical report 
- **html.py**:
    - Called by fusion_template.html
    - Assembles tables to be rendered
- **constants.py**:
    - Called by various files
    - Contains constants shared throughout the plugin
- **test/**
    - A directory containing all data to run the fusion plugin test  

## Preprocess Filtering 

### Preprocessing Mavis

The function that preprocesses the mavis file is preprocess.py/process_mavis

The following filtering steps are applied to the mavis output ${tumour_id}.mavis_summary.tab:
1. **self.add_tumour_id**: A column called "Sample" is added. This is a column with the tumour ID for every row.
2. **self.split_column_take_max**: Performs some necessary data wrangling on certain reads columns (see function for details) to prepare it for filtering by read support.
3. **self.add_filter_sortby_read_support**: A read support column is added based on the call_method column. Then, the fusions are filtered by read support. Only fusions with read supprt > 20 (not >=) are kept.
4. **self.add_translocation_notation**: Using the chromosomes of the two genes in the fusion, a translocation column is added (ex. "t(14;X)") if the event type is "translocation" or "inverted translocation". 
5. **self.add_dna_rna_support**: Two columns, DNA_support (tool = delly) and RNA support (tool = starfusion or arriba), are added, with yes if there is DNA/RNA support and no if there isn't. This is used for ease of interpretation. 
6. **self.write_fusion_pairs**: A column is made to concatenate gene1-gene2 without care for 5' or 3' end. Fusion pairs are written alphabetically (ex. FGFR-KRAS) for merging with arriba data and deduplicating.

This function outputs a filtered df_mavis dataframe.

### Preprocessing Arriba

The function that preprocesses the arriba file is preprocess.py/process_arriba

The following filtering steps are applied to the arriba output ${tumour_id}.fusions.tsv:
1. **self.change_column_name**: The column name "#gene1" is changed to "gene1" to make it consistent with column name "gene2"
2. **self.write_fusion_pairs**: A column is made to concatenate gene1-gene, and they are sorted alphabetically for merging with mavis data and deduplicating.

This function outputs a filtered df_arriba dataframe.

### Merging Mavis and Arriba

The function that merges mavis and arriba data and writes the fusion files is preprocess.py/write_fusion_files with an inner function called **self.merge_mavis_arriba**

The following steps occur in **self.merge_mavis_arriba**:
1. **self.left_join**: Mavis and arriba data are merged using a **left join** (if a mavis entry matches an arriba entry, the arriba data is added to the mavis data).
2. **self.fix_reading_frames**: If a reading frame is 
3. **self.drop_duplicates_merge_columns**: Drops duplicate fusions (ex. if FGFR2-KRAS appears twice) but merge the event type and reading frame columns (sometimes the same fusion can have multiple event types and frames; we want to preserve that information)
4. **self.remove_self_fusions**: Removes fusion pairs of genes with themselves (ex. "CDKN2A-CDKN2A")
5. **self.simplify_reading_frame**: Replaces "." reading frame with the word "Unknown". Also creates a new column called "reading frame simple" where if a fusion has multiple reading frames (ex. "out-of-frame;in-frame"), it will replace it will "Multiple Frames"
6. **self.simplify_event_type**: Creates a new column called "event_type_simple". If there are multiple event types (mavis and arriba can't determine which one is correct, ex. "inversion;duplication"), it will replace it with "Undetermined". If the event type contains translocation or inverted translocation, it will replace it with the translocation notation. If the event type contains "inversion", it will replace it with the inversion notation (ex. inv(17)). 
7. **self.reorder_fusions**: Fusions are re-ordered in 5'-3' order based on the "gene1_direction" and "gene2_direction" columns
8. **self.delete_delly_only_calls**: Deletes delly only calls, as structural variants are not validated (according to legacy R code)
   
### Annotating OncoKB and NCCN variants 

The function that writes the files is still preprocess.py/write_fusion_files

It does the following after merging mavis and arriba:
1. **self.process_nccn**: Filters data for only NCCN fusions (as described in djerba/data/NCCN_annotations.txt). 
2. **self.df_for_oncokb_annotator**: Prepares the data for the oncokb annotator. 
3. Outputs data_fusions.txt (for interpretation), data_fusions_NCCN.txt (for oncokb annotator), and data_fusions_oncokb.txt (for oncokb annotator) to the workspace.

## Additional filtering in tools.py

There is some minor filtering that happens when generating the fusion counts:
- **Clinically relevant variants**: this number is calculated from data_fusions_oncokb_annotated.txt. It only counts those entries for which the mutation effect is not "Unknown".
- **NCCN relevant variants**: this number is calculated from data_fusions_NCCN.txt, and only counts those fusions for which the fusion is not a Gene-None or None-Gene fusion. It does not care if those fusions have Unknown effect or not, only that there are NCCN fusions.
- **Total variants**: this number is calculated from data_fusions.txt. "None" fusions are counted as 1 gene. Ex. if "FGFR2-KRAS" and "CDKN2A-None" fusions were found, the count would be 3.

## History

See the [changelog](./CHANGELOG.md) for a detailed development history. In brief:

- **2025-03**: Created this README.md

