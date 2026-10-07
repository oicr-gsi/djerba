# Simplified IgCaller Translocation Filtering Guide for CGI

## Purpose

This document explains the simplified IgCaller filtering script that was prepared for CGI review:

```text
scripts/simplified_igcaller_translocation_filters_for_collaborator.R
```

The script can start from the raw
IgCaller `*_output_filtered.tsv` files, add the parsed/cytoband/sample metadata
columns required by the project table, and then reproduce the main automated
filters used to generate candidate multiple myeloma Ig translocation calls.

If the raw IgCaller files are not available, the script can also fall back to
the cached parsed table:

```text
Ig_caller_df_cfWGS_filtered_MM_only_filtered_Ig_caller_outputs_updated2.rds
```

The script also optionally applies the manual IGV review workbook to generate
the final binary cytoband-level feature matrix used downstream.

## What This Script Does

The simplified script performs five steps.

1. Look for raw IgCaller `*_output_filtered.tsv` files in `raw_igcaller_dir`.
2. If raw files are present, parse translocation rows and add the columns needed
   for the project table.
3. If raw files are absent, load the cached parsed/annotated RDS.
4. Apply score, mappability, myeloma-gene, and common-MM-translocation filters.
5. Remove calls with breakpoints in ENCODE hg38 blacklist regions.
6. Remove likely recurrent cohort artifacts.
7. Export:
   - all automated filtered calls,
   - candidate common-MM calls for IGV review,
   - IGV-confirmed calls if the review workbook is available,
   - the final simplified cytoband-level matrix.

## What This Script Does Not Do

This script does not rerun IgCaller from BAM files.

It does reproduce the key parsing and annotation columns needed for downstream
filtering when raw IgCaller `*_output_filtered.tsv` files are supplied. The raw
files are not present in this local checkout, so the default local run falls back
to the cached parsed and annotated IgCaller object.

The full upstream parser remains:

```text
Scripts_2025/Final_Scripts/1_3_Process_Ig_Translocation_Info.R
```

## Upstream IgCaller Command Thresholds

The upstream IgCaller launcher used the following key command-line settings:

```bash
python3 IgCaller \
  -seq wgs \
  -mntoncoPass 2 \
  -mntonco 1 \
  -p 0.05 \
  --maxNumberReadsNormalOncoIg 8 \
  -kmb yes
```

Interpretation:

| Parameter | Value | Meaning in this workflow |
|---|---:|---|
| `-seq` | `wgs` | Whole-genome sequencing mode |
| `-mntoncoPass` | `2` | IgCaller pass-level threshold for tumour/onco-Ig evidence |
| `-mntonco` | `1` | IgCaller tumour/onco-Ig evidence threshold |
| `-p` | `0.05` | IgCaller probability or p-value style threshold used by the caller |
| `--maxNumberReadsNormalOncoIg` | `8` | Maximum normal onco-Ig read support allowed |
| `-kmb` | `yes` | Keep memory/bam-related IgCaller option enabled in the original run |

These are caller-level thresholds. The rest of this document describes the
additional downstream filters applied after IgCaller has already produced calls.

## Main Input Files

### 1. Raw IgCaller output directory

Default path:

```text
Oct 2024 data/Ig_caller
```

Expected files:

```text
*_output_filtered.tsv
```

or:

```text
*_filtered.tsv
```

When this directory exists and contains matching files, the script uses raw mode.
Raw mode parses lines containing `Translocation` and extracts the same fixed
IgCaller columns used by the full pipeline:

| Parsed field | Source column position in raw IgCaller line |
|---|---:|
| `breakpoint1` | 5 |
| `breakpoint1_strand` | 6 |
| `breakpoint2` | 7 |
| `breakpoint2_strand` | 8 |
| `gene1` | 9 |
| `gene2` | 10 |
| `IGCaller_Score` | 12 |
| `Mappability_Issue` | 15 |

Raw mode then adds:

| Added column | How it is created |
|---|---|
| `Bam_File` | From the raw filename, replacing `_output_filtered.tsv` with `.bam` |
| `break1_chromosome`, `break1_position_start`, `break1_position_end` | Parsed from `breakpoint1` |
| `break2_chromosome`, `break2_position_start`, `break2_position_end` | Parsed from `breakpoint2` |
| `break1_cytoband`, `break2_cytoband` | Matched against the cytoband file |
| `Potential_MM_translocation` | chr14 paired with chr4/6/8/11/16/20 in either orientation |
| `Sorted_translocation` | Canonical cytoband-pair label independent of breakpoint order |
| `Common_MM_translocation` | Match to canonical MM cytoband-pair list |
| `Recurrent_TRA` | chr14q32.33 plus recurrent partner cytoband |
| `Patient` and sample metadata | Joined from `metadata_csv` when available |

The raw-mode parsed table is exported as:

```text
igcaller_raw_parsed_annotated_mm_only_calls.tsv
igcaller_raw_parsed_annotated_mm_only_calls.rds
```

### 2. Cytoband file

Default path:

```text
Oct 2024 data/cytoBand.txt
```

This is required in raw mode. It is used to convert breakpoint coordinates into
cytoband labels such as `chr14q32.33`.

### 3. Metadata CSV

Default path:

```text
combined_clinical_data_updated_Feb5_2025.csv
```

This is optional but recommended in raw mode. If present, calls are joined on:

```r
Bam_File == Bam
```

If absent, the script still runs and uses `Bam_File` as a conservative surrogate
for `Patient` during recurrent-artifact counting.

### 4. Parsed annotated IgCaller table

Default path:

```text
Output_tables_2025/translocation_processing_support/Ig_caller_df_cfWGS_filtered_MM_only_filtered_Ig_caller_outputs_updated2.rds
```

This object contains parsed IgCaller calls plus metadata and annotation columns.
Required columns include:

| Column | Purpose |
|---|---|
| `break1_chromosome`, `break1_position_start`, `break1_position_end` | First breakpoint location |
| `break2_chromosome`, `break2_position_start`, `break2_position_end` | Second breakpoint location |
| `gene1`, `gene2` | Genes reported by IgCaller |
| `IGCaller_Score` | IgCaller score used in downstream thresholding |
| `Mappability_Issue` | Whether IgCaller flagged mappability concerns |
| `Common_MM_translocation` | Binary flag for canonical MM translocation cytobands |
| `Potential_MM_translocation` | Binary flag for potential MM-relevant Ig translocation |
| `Sorted_translocation` | Cytoband pair used for the final matrix |
| `Bam_File` | Sample-level BAM identifier |

### 5. ENCODE hg38 blacklist BED

Default path:

```text
hg38-blacklist.v2.bed
```

Any call is removed if either breakpoint overlaps the blacklist.

### 6. Manual IGV review workbook

Default path:

```text
Jan2025_exported_data/Ig_caller_df_cfWGS_filtered_aggressive2_iGV_check.xlsm
```

This workbook contains the manual review column:

| Column | Use |
|---|---|
| `Looks_real` | Manual IGV confidence or binary call; final translocation matrix uses `Looks_real == 1` |

For the separate disease-evidence override, the project uses `Looks_real > 0.7`.
That is intentionally less strict than the final translocation feature matrix.

## Automated Filtering Logic

The core automated filter keeps a call if it passes at least one of the following
evidence rules:

| Rule | Keep condition | Rationale |
|---|---|---|
| High-score mappability-flagged call | `Mappability_Issue != "none"` and `IGCaller_Score >= 100` | Low-mappability calls need stronger evidence |
| Standard clean-region call | `Mappability_Issue == "none"` and `IGCaller_Score >= 50` | Clean regions can use the standard score threshold |
| Common MM translocation rescue | `Common_MM_translocation == 1` and `IGCaller_Score > 15` | Canonical MM events have high prior biological plausibility |
| Myeloma-gene rescue | `Other_gene` is in the relevant myeloma gene list | Avoid dropping known MM driver partners solely by score |

After that, the call must also satisfy:

```r
Potential_MM_translocation == 1 | Other_gene %in% relevant_myeloma_genes
```

This keeps the call set focused on Ig/myeloma-relevant events.

## Relevant Myeloma Gene List

The broader relevant-gene list used for rescue is:

```text
FGFR3, NSD2, WHSC1,
CCND1, CDK6, BCL1,
MAF, MAFB, ITGB7,
MYC, PVT1, TMPO,
CCND3, BMP6, DUSP22,
IRF4, CDKN2C,
BCL2, BCL9
```

The smaller key-gene list used when deciding whether recurrent gene pairs should
be retained is:

```text
CCND1, FGFR3, NSD2, MAF, MAFB, MYC, CCND3, IRF4
```

## Blacklist Filtering

The script removes a call if either breakpoint overlaps an ENCODE hg38 blacklist
region.

Reason:

Blacklist regions are more likely to produce mapping artifacts, high-signal
artifacts, or ambiguous breakpoint evidence. Removing any call where either side
overlaps the blacklist is conservative.

## Recurrent Artifact Filtering

The script removes likely recurrent technical artifacts in two ways.

### LOC/LINC filter

Calls involving `Other_gene` names beginning with `LOC` or `LINC` are removed if:

```r
IGCaller_Score <= 200
```

Reason:

These loci are often difficult to interpret and can recur in lower-confidence
regions. The script only keeps them if IgCaller score is very high.

### Patient-frequency filter

For each `IG_gene` and `Other_gene` pair, the script computes:

```r
patient_count = number of distinct patients with the pair
```

It keeps pairs if:

```r
patient_count <= 2
```

or if:

```r
Other_gene is a key myeloma gene AND Common_MM_translocation == 1
```

Reason:

Many different patients sharing the same non-canonical IgCaller pair is more
suspicious for a recurrent mapping artifact. However, recurrent canonical MM
events involving key myeloma genes are biologically expected and are retained.

## Final Extra-Strict Pass

After the earlier filtering, the script applies one final stricter pass:

Remove:

```r
Mappability_Issue != "none" & IGCaller_Score <= 100
```

Remove weak `NSD2` or `MAF` calls:

```r
IGCaller_Score <= 20 & Other_gene %in% c("NSD2", "MAF")
```

Then keep only calls satisfying at least one of:

```r
Mappability_Issue == "none" & IGCaller_Score >= 50
Common_MM_translocation == 1 & IGCaller_Score >= 40
Other_gene %in% relevant_myeloma_genes
```

This final pass is the simplified equivalent of the project object named:

```text
Jan_2025_Ig_caller_df_cfWGS_filtered_extra_aggressive.rds
```

## IGV Review Step

The automated filters are not treated as final truth for the manuscript-facing
translocation matrix.

The final matrix uses only calls from the IGV review workbook where:

```r
Looks_real == 1
```

This produces:

```text
translocation_data_cytoband_updated_simplified.tsv
translocation_data_cytoband_updated_simplified.rds
```

The matrix contains binary columns:

| Column | Meaning |
|---|---|
| `IGH_CCND1` | t(11;14)-like event |
| `IGH_FGFR3` | t(4;14)-like event |
| `IGH_MAF` | t(14;16)-like event |
| `IGH_MYC` | t(8;14)-like event |

## Output Files

Default output directory:

```text
Output_tables_2025/igcaller_cgi_simplified
```

### `igcaller_automated_extra_aggressive_calls.tsv`

All calls passing the simplified automated downstream filters.

Use this file to inspect the post-filtered call set before manual IGV review.

### `igcaller_candidate_common_mm_calls_for_igv_review.tsv`

Subset of automated filtered calls that are:

```r
Common_MM_translocation == 1
```

and, if the metadata column is present:

```r
timepoint_info %in% c("Baseline", "Diagnosis")
```

Use this file as the simplest candidate table for CGI review.

### `igcaller_igv_confirmed_calls.tsv`

Calls from the review workbook with:

```r
Looks_real == 1
```

This is the source for the final binary translocation feature matrix.

### `igcaller_evidence_override_samples_looks_real_gt_0_7.tsv`

Samples from the review workbook with:

```r
Looks_real > 0.7
```

These are used in the broader project as disease-evidence overrides, not as the
strict final translocation matrix.

### `translocation_data_cytoband_updated_simplified.tsv`

Final simplified cytoband-level matrix built from `Looks_real == 1` calls.

This is the easiest file to use for downstream binary feature integration.

### `igcaller_filter_qc_summary.tsv`

Small QC summary with row and patient counts after each major step.

In the current local run, the key counts were:

| Metric | Value |
|---|---:|
| Annotated input rows | 64,317 |
| Automated filtered rows | 499 |
| Candidate common-MM baseline/diagnosis rows | 20 |
| Automated filtered unique patients | 54 |
| Candidate unique patients | 11 |
| IGV-confirmed `Looks_real == 1` rows | 4 |
| IGV-confirmed unique patients | 3 |

## How To Run

From the project root:

```bash
Rscript scripts/simplified_igcaller_translocation_filters_for_collaborator.R
```

With explicit input and output paths:

```bash
Rscript scripts/simplified_igcaller_translocation_filters_for_collaborator.R \
  raw_igcaller_dir=path/to/IgCaller_outputs \
  cytoband_file=path/to/cytoBand.txt \
  metadata_csv=path/to/clinical_metadata.csv \
  blacklist_bed=path/to/hg38-blacklist.v2.bed \
  igv_review_xlsm=path/to/Ig_caller_df_cfWGS_filtered_aggressive2_iGV_check.xlsm \
  output_dir=cgi_igcaller_outputs
```

To force use of an already parsed/annotated RDS instead of raw files, point
`raw_igcaller_dir` to a missing or empty directory and pass:

```bash
Rscript scripts/simplified_igcaller_translocation_filters_for_collaborator.R \
  annotated_igcaller_rds=path/to/annotated_igcaller.rds \
  blacklist_bed=path/to/hg38-blacklist.v2.bed \
  igv_review_xlsm=path/to/Ig_caller_df_cfWGS_filtered_aggressive2_iGV_check.xlsm \
  raw_igcaller_dir=/tmp/no_raw_igcaller_files \
  output_dir=cgi_igcaller_outputs_from_rds
```

Arguments are passed as `key=value` pairs.

## Recommended File To Open First

For reviewing candidate calls:

```text
Output_tables_2025/igcaller_cgi_simplified/igcaller_candidate_common_mm_calls_for_igv_review.tsv
```

For the final binary call matrix:

```text
Output_tables_2025/igcaller_cgi_simplified/translocation_data_cytoband_updated_simplified.tsv
```

For all automated filtered calls:

```text
Output_tables_2025/igcaller_cgi_simplified/igcaller_automated_extra_aggressive_calls.tsv
```

## Important Interpretation Notes

The automated filtered calls are candidates, not final curated calls.

The final translocation feature matrix requires manual IGV confirmation with
`Looks_real == 1`.

The `Looks_real > 0.7` threshold is used only for a broader disease-evidence
override in the larger project. It should not be confused with the stricter final
translocation matrix threshold.

The raw IgCaller `*_output_filtered.tsv` files are not currently present in this
local checkout. The simplified script therefore starts from the parsed annotated
RDS object that was produced by the full upstream pipeline.

## Expected Failure Modes

### Missing parsed IgCaller RDS

The script will stop with a clear missing-file error. Provide
`annotated_igcaller_rds=...`.

### Missing blacklist BED

The script will stop because blacklist filtering is part of the defined call set.
Provide `blacklist_bed=...`.

### Missing IGV review workbook

The script will still write the automated filtered files, but it will skip the
IGV-confirmed final matrix.

### Missing required columns

The script validates required columns early and stops if the input table does not
match the expected schema.

## Provenance Summary

This simplified guide corresponds to the implemented filtering logic in:

```text
Scripts_2025/Final_Scripts/1_3_Process_Ig_Translocation_Info.R
Scripts_2025/Final_Scripts/1_5_Integrate_WGS_Feature_Data.R
Run_Igcaller_WGS.sh
```

The simplified script is intended for transparent review and sharing, not as a
replacement for the full manuscript pipeline.
