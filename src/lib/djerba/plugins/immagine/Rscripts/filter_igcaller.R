# # Author: DORY ABELMAN (Dory.Abelman@uhn.ca)

# # Simplified IgCaller Translocation Filtering Workflow
#
# ## Why this script exists
#
# This is a simplified version of the IgCaller downstream
# filtering workflow used in this project. It is designed to be readable as a
# methods handoff as well as executable R code.
#
# The full manuscript pipeline has a longer historical parsing and figure-making
# context. This script keeps only the core call-filtering logic:
#
# 1. Start from either:
#    - raw IgCaller `*_output_filtered.tsv` files, or
#    - the already parsed/cytoband-annotated IgCaller RDS cache.
# 2. If raw files are supplied, parse them and add the columns needed to match
#    the project table
#    `Ig_caller_df_cfWGS_filtered_MM_only_filtered_Ig_caller_outputs_updated2.rds`.
# 3. Apply the automated score, mappability, gene-prior, blacklist, and artifact
#    filters used in the project.
# 4. Export a candidate table for IGV review.
# 5. If the manual IGV workbook is present, export the final IGV-confirmed
#    cytoband-level binary translocation matrix.
#
# ## What this script is not
#
# This script does **not** rerun IgCaller from BAM files.
#
# This script can re-parse the original raw IgCaller `*_output_filtered.tsv`
# files if they are supplied with `raw_igcaller_dir=...`.
#
# In this local checkout those raw filtered TSV files are not present, so the
# default run starts from the cached parsed/annotated IgCaller object produced by
# the full upstream workflow.
#
# ## Upstream IgCaller command used for calling
#
# IgCaller was run upstream with the following core thresholds/options:
#
# ```bash
# python3 IgCaller \
#   -seq wgs \
#   -mntoncoPass 2 \
#   -mntonco 1 \
#   -p 0.05 \
#   --maxNumberReadsNormalOncoIg 8 \
#   -kmb yes
# ```
#
# These are caller-level parameters. The rest of this script applies additional
# downstream filters to the IgCaller output.
#
# | Parameter | Value | Practical interpretation here |
# |---|---:|---|
# | `-seq` | `wgs` | Whole-genome sequencing mode |
# | `-mntoncoPass` | `2` | IgCaller pass-level tumour/onco-Ig support setting |
# | `-mntonco` | `1` | IgCaller tumour/onco-Ig support setting |
# | `-p` | `0.05` | IgCaller probability/p-value style threshold |
# | `--maxNumberReadsNormalOncoIg` | `8` | Maximum onco-Ig read evidence allowed in matched normal |
# | `-kmb` | `yes` | Original IgCaller run option retained from project run |
#
# ## Inputs
#
# ### `annotated_igcaller_rds`
#
# Parsed, cytoband-annotated IgCaller calls with sample metadata and the project
# annotation columns `Common_MM_translocation` and `Potential_MM_translocation`.
#
# Default:
#
# ```text
# Output_tables_2025/translocation_processing_support/
# Ig_caller_df_cfWGS_filtered_MM_only_filtered_Ig_caller_outputs_updated2.rds
# ```
#
# ### `raw_igcaller_dir`
#
# Optional directory containing raw IgCaller output files:
#
# ```text
# *_output_filtered.tsv
# ```
#
# If this directory contains matching files, the script parses them and creates
# the columns required for downstream filtering. This is the recommended mode
# for CGI if they have the original IgCaller outputs.
#
# Default:
#
# ```text
# Oct 2024 data/Ig_caller
# ```
#
# ### `cytoband_file`
#
# Required when parsing raw IgCaller outputs. UCSC-style cytoband table with
# chromosome, start, end, band, and stain columns.
#
# Default:
#
# ```text
# Oct 2024 data/cytoBand.txt
# ```
#
# ### `metadata_csv`
#
# Optional clinical/sample metadata table used to add `Patient`, `Sample_type`,
# `Timepoint`, `Sample_ID`, and related columns by joining raw IgCaller calls on
# `Bam_File == Bam`.
#
# If this file is unavailable, the script still runs, but it uses `Bam_File` as
# the patient-count unit for recurrent-artifact filtering. That is acceptable for
# transparent review, but less exact than the project metadata join.
#
# Default:
#
# ```text
# combined_clinical_data_updated_Feb5_2025.csv
# ```
#
# Required columns include:
#
# | Column | Role |
# |---|---|
# | `break1_chromosome`, `break1_position_start`, `break1_position_end` | First breakpoint |
# | `break2_chromosome`, `break2_position_start`, `break2_position_end` | Second breakpoint |
# | `gene1`, `gene2` | Genes reported by IgCaller |
# | `IGCaller_Score` | Caller score used by downstream thresholds |
# | `Mappability_Issue` | IgCaller mappability warning field |
# | `Common_MM_translocation` | Canonical MM cytoband translocation flag |
# | `Potential_MM_translocation` | Broader MM-relevant Ig translocation flag |
# | `Sorted_translocation` | Cytoband pair used for final feature labels |
# | `Bam_File` | Sample-level BAM filename |
#
# ### `blacklist_bed`
#
# ENCODE hg38 blacklist BED. A call is removed if **either** breakpoint overlaps
# a blacklist interval.
#
# Default:
#
# ```text
# hg38-blacklist.v2.bed
# ```
#
# ### `igv_review_xlsm`
#
# Manual IGV review workbook. The final translocation feature matrix uses only:
#
# ```r
# Looks_real == 1
# ```
#
# The broader project uses `Looks_real > 0.7` only as an evidence-of-disease
# override; that is intentionally less strict than the final translocation
# matrix.
#
# Default:
#
# ```text
# Jan2025_exported_data/Ig_caller_df_cfWGS_filtered_aggressive2_iGV_check.xlsm
# ```
#
# ## Automated filtering rules
#
# The first automated pass keeps a call if **any** of these conditions are true:
#
# | Rule | Keep condition | Reason |
# |---|---|---|
# | High-score mappability-flagged call | `Mappability_Issue != "none" & IGCaller_Score >= 100` | Low-mappability regions need stronger support |
# | Clean-region standard call | `Mappability_Issue == "none" & IGCaller_Score >= 50` | Standard threshold for clean regions |
# | Common MM rescue | `Common_MM_translocation == 1 & IGCaller_Score > 15` | Canonical MM events have high biological prior |
# | Relevant MM gene rescue | `Other_gene %in% relevant_myeloma_genes` | Avoid dropping known MM drivers solely by score |
#
# Then the call must also satisfy:
#
# ```r
# Potential_MM_translocation == 1 | Other_gene %in% relevant_myeloma_genes
# ```
#
# ## Artifact and blacklist filters
#
# After the score/gene-prior pass, the script removes:
#
# 1. Calls where either breakpoint overlaps the ENCODE hg38 blacklist.
# 2. `LOC*` or `LINC*` partner calls unless `IGCaller_Score > 200`.
# 3. Gene pairs seen in more than two patients, unless the partner is a key MM
#    gene and the call is a canonical common-MM translocation.
#
# The patient-frequency filter is meant to reduce recurrent mapping artifacts,
# while still preserving biologically expected recurrent MM translocations.
#
# ## Final extra-strict automated pass
#
# The script then removes:
#
# ```r
# Mappability_Issue != "none" & IGCaller_Score <= 100
# IGCaller_Score <= 20 & Other_gene %in% c("NSD2", "MAF")
# ```
#
# and keeps only calls satisfying at least one of:
#
# ```r
# Mappability_Issue == "none" & IGCaller_Score >= 50
# Common_MM_translocation == 1 & IGCaller_Score >= 40
# Other_gene %in% relevant_myeloma_genes
# ```
#
# This is the simplified equivalent of the project object:
#
# ```text
# Jan_2025_Ig_caller_df_cfWGS_filtered_extra_aggressive.rds
# ```
#
# ## Outputs
#
# Default output directory:
#
# ```text
# Output_tables_2025/igcaller_cgi_simplified
# ```
#
# | Output file | What it is |
# |---|---|
# | `igcaller_automated_extra_aggressive_calls.tsv` | All calls passing automated filters |
# | `igcaller_candidate_common_mm_calls_for_igv_review.tsv` | Common-MM baseline/diagnosis candidate calls for IGV review |
# | `igcaller_igv_confirmed_calls.tsv` | Calls from the manual workbook with `Looks_real == 1` |
# | `igcaller_evidence_override_samples_looks_real_gt_0_7.tsv` | Samples used for broader evidence-of-disease override |
# | `translocation_data_cytoband_updated_simplified.tsv` | Final binary cytoband-level matrix from `Looks_real == 1` |
# | `igcaller_filter_qc_summary.tsv` | Row and patient counts for QC |
#
# ## Recommended file to open first
#
# For reviewing candidate calls:
#
# ```text
# Output_tables_2025/igcaller_cgi_simplified/
# igcaller_candidate_common_mm_calls_for_igv_review.tsv
# ```
#
# For the final binary feature matrix:
#
# ```text
# Output_tables_2025/igcaller_cgi_simplified/
# translocation_data_cytoband_updated_simplified.tsv
# ```
#
# ## How to run
#
# From the project root:
#
# ```bash
# Rscript scripts/simplified_igcaller_translocation_filters_for_collaborator.R
# ```
#
# With explicit paths:
#
# ```bash
# Rscript scripts/simplified_igcaller_translocation_filters_for_collaborator.R \
#   raw_igcaller_dir=path/to/IgCaller_outputs \
#   cytoband_file=path/to/cytoBand.txt \
#   metadata_csv=path/to/clinical_metadata.csv \
#   blacklist_bed=path/to/hg38-blacklist.v2.bed \
#   igv_review_xlsm=path/to/Ig_caller_df_cfWGS_filtered_aggressive2_iGV_check.xlsm \
#   output_dir=cgi_igcaller_outputs
# ```
#
# Or, using the cached parsed/annotated RDS instead of raw files:
#
# ```bash
# Rscript scripts/simplified_igcaller_translocation_filters_for_collaborator.R \
#   annotated_igcaller_rds=path/to/annotated_igcaller.rds \
#   blacklist_bed=path/to/hg38-blacklist.v2.bed \
#   igv_review_xlsm=path/to/Ig_caller_df_cfWGS_filtered_aggressive2_iGV_check.xlsm \
#   output_dir=cgi_igcaller_outputs
# ```
#
# ## Interpretation cautions
#
# Automated filtered calls are **candidate calls**, not final curated calls.
#
# The strict final matrix uses manual IGV-confirmed calls with `Looks_real == 1`.
#
# The raw IgCaller filtered files are not included in this checkout, so this
# script starts from the parsed and annotated RDS cache.
#
# A longer plain-language guide is also available here:
#
# ```text
# docs/igcaller_cgi_filtering_guide.md
# ```

rm(list=ls())
suppressPackageStartupMessages({
  library(optparse)
  library(dplyr)
  library(readr)
  library(stringr)
  library(tidyr)
})


# command line options
option_list = list(
  make_option(c("-i", "--base_dir"), type="character", default=NULL, help="cBioWrap base directory", metavar="character"),
  make_option(c("-r", "--raw_igcaller_dir"), type="character", default=NULL, help="zipped igcaller results", metavar="character"),
  make_option(c("-c", "--cytoband_file"), type="character", default=NULL, help="cytoband file", metavar="character"),
  make_option(c("-b", "--blacklist_bed"), type="character", default=NULL, help="hg38 blacklist bed file", metavar="character"),
  make_option(c("-o", "--output_dir"), type="character", default=NULL, help="output directory", metavar="character")
)


# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE);
opt <- parse_args(opt_parser);

# set better variable names
base_dir <- opt$base_dir
raw_igcaller_dir <- opt$raw_igcaller_dir
cytoband_file <- opt$cytoband_file
blacklist_bed <- opt$blacklist_bed
output_dir <- opt$output_dir



`%||%` <- function(x, y) {
  if (is.null(x) || identical(x, "")) y else x
}

config <- list(
  raw_igcaller_dir = raw_igcaller_dir,
  cytoband_file = cytoband_file,
  #metadata_csv = metadata_csv,
  #annotated_igcaller_rds = annotated_igcaller_rds
  blacklist_bed = blacklist_bed,
  #igv_review_xlsm = args$igv_review_xlsm %||%
  output_dir = output_dir %||% file.path("Output_tables_2025", "igcaller_cgi_simplified")
)

required_columns <- c(
  "break1_chromosome", "break1_position_start", "break1_position_end",
  "break2_chromosome", "break2_position_start", "break2_position_end",
  "gene1", "gene2", "IGCaller_Score", "Mappability_Issue",
  "Bam_File", "Common_MM_translocation", "Potential_MM_translocation",
  "Sorted_translocation"
)

relevant_myeloma_genes <- c(
  "FGFR3", "NSD2", "WHSC1",
  "CCND1", "CDK6", "BCL1",
  "MAF", "MAFB", "ITGB7",
  "MYC", "PVT1", "TMPO",
  "CCND3", "BMP6", "DUSP22",
  "IRF4", "CDKN2C",
  "BCL2", "BCL9"
)

key_myeloma_genes <- c("CCND1", "FGFR3", "NSD2", "MAF", "MAFB", "MYC", "CCND3", "IRF4")

myeloma_translocations <- c(
  "chr11q13.3_chr14q32.33",
  "chr14q32.33_chr16q23.2",
  "chr14q32.33_chr16q23.1", # adding IGH:WWOX as it is used as a proxy for MAF
  "chr14q32.33_chr20q13.33",
  "chr11q13.2_chr14q32.33",
  "chr14q32.33_chr4p16.3",
  "chr14q32.33_chr6q21",
  "chr14q32.33_chr8q24.21",
  "chr14q32.33_chr6p21"
)

stop_if_missing <- function(path, label) {
  if (!file.exists(path)) {
    stop("Missing ", label, ": ", path, call. = FALSE)
  }
}

validate_columns <- function(data, columns, label) {
  missing_columns <- setdiff(columns, names(data))
  if (length(missing_columns) > 0L) {
    stop(
      label, " is missing required columns:\n  ",
      paste(missing_columns, collapse = "\n  "),
      call. = FALSE
    )
  }
  invisible(data)
}

standardize_ig_partner <- function(data) {
  data %>%
    mutate(
      IG_gene = case_when(
        str_starts(gene1, "IG") ~ gene1,
        str_starts(gene2, "IG") ~ gene2,
        TRUE ~ NA_character_
      ),
      Other_gene = case_when(
        str_starts(gene1, "IG") ~ gene2,
        str_starts(gene2, "IG") ~ gene1,
        TRUE ~ NA_character_
      )
    )
}

read_blacklist_bed <- function(path) {
  bed <- read_tsv(
    path,
    col_names = FALSE,
    col_types = cols(.default = col_character()),
    comment = "#"
  )

  if (ncol(bed) < 3L) {
    stop("Blacklist BED must have at least three columns: ", path, call. = FALSE)
  }

  bed <- bed[, seq_len(min(ncol(bed), 4L)), drop = FALSE]
  names(bed) <- c("chrom", "start", "stop", "description")[seq_len(ncol(bed))]

  bed <- bed %>%
    filter(!(row_number() == 1L & !str_detect(start, "^[0-9]+$"))) %>%
    mutate(
      start = suppressWarnings(as.numeric(start)),
      stop = suppressWarnings(as.numeric(stop))
    )

  if (any(is.na(bed$chrom) | is.na(bed$start) | is.na(bed$stop))) {
    stop("Blacklist BED contains missing chrom/start/stop values: ", path, call. = FALSE)
  }

  bed %>%
    mutate(chrom = if_else(str_starts(chrom, "chr"), chrom, paste0("chr", chrom)))
}

read_cytoband_file <- function(path) {
  stop_if_missing(path, "cytoband file")

  cytobands <- read_tsv(
    path,
    col_names = FALSE,
    col_types = cols(.default = col_character()),
    comment = "#"
  )

  if (ncol(cytobands) < 4L) {
    stop("Cytoband file must have at least four columns: ", path, call. = FALSE)
  }

  cytobands <- cytobands[, seq_len(min(ncol(cytobands), 5L)), drop = FALSE]
  names(cytobands) <- c("chr", "start", "end", "band", "stain")[seq_len(ncol(cytobands))]

  cytobands <- cytobands %>%
    filter(!(row_number() == 1L & !str_detect(start, "^[0-9]+$"))) %>%
    mutate(
      chr = if_else(str_starts(chr, "chr"), chr, paste0("chr", chr)),
      start = suppressWarnings(as.numeric(start)),
      end = suppressWarnings(as.numeric(end))
    )

  if (any(is.na(cytobands$chr) | is.na(cytobands$start) | is.na(cytobands$end))) {
    stop("Cytoband file contains missing chr/start/end values: ", path, call. = FALSE)
  }

  cytobands
}

match_cytoband <- function(chromosome, position_start, cytobands) {
  chromosome <- if_else(str_starts(as.character(chromosome), "chr"), as.character(chromosome), paste0("chr", chromosome))
  position_start <- as.numeric(position_start)

  vapply(seq_along(chromosome), function(i) {
    if (is.na(chromosome[[i]]) || is.na(position_start[[i]])) {
      return(NA_character_)
    }
    matched <- cytobands %>%
      filter(chr == chromosome[[i]], start <= position_start[[i]], end >= position_start[[i]]) %>%
      slice(1)
    if (nrow(matched) == 0L) {
      NA_character_
    } else {
      if (is.na(matched$band[[1]]) || matched$band[[1]] == "") {
        matched$chr[[1]]
      } else {
        paste0(matched$chr[[1]], matched$band[[1]])
      }
    }
  }, character(1))
}

sort_translocation <- function(translocation) {
  vapply(translocation, function(x) {
    parts <- strsplit(as.character(x), "_", fixed = TRUE)[[1]]
    paste(sort(parts), collapse = "_")
  }, character(1))
}

split_breakpoint <- function(breakpoint) {
  pieces <- strsplit(as.character(breakpoint), ":", fixed = TRUE)
  chrom <- vapply(pieces, function(x) if (length(x) >= 1L) x[[1]] else NA_character_, character(1))
  pos <- vapply(pieces, function(x) if (length(x) >= 2L) x[[2]] else NA_character_, character(1))
  tibble(chromosome = chrom, position = suppressWarnings(as.numeric(pos)))
}

add_potential_mm_translocation <- function(data) {
  data %>%
    mutate(
      Potential_MM_translocation = if_else(
        (break1_chromosome == "chr11" & break2_chromosome == "chr14") |
          (break1_chromosome == "chr14" & break2_chromosome == "chr11") |
          (break1_chromosome == "chr4" & break2_chromosome == "chr14") |
          (break1_chromosome == "chr14" & break2_chromosome == "chr4") |
          (break1_chromosome == "chr14" & break2_chromosome == "chr16") |
          (break1_chromosome == "chr16" & break2_chromosome == "chr14") |
          (break1_chromosome == "chr14" & break2_chromosome == "chr20") |
          (break1_chromosome == "chr20" & break2_chromosome == "chr14") |
          (break1_chromosome == "chr6" & break2_chromosome == "chr14") |
          (break1_chromosome == "chr14" & break2_chromosome == "chr6") |
          (break1_chromosome == "chr8" & break2_chromosome == "chr14") |
          (break1_chromosome == "chr14" & break2_chromosome == "chr8"),
        1L,
        0L
      )
    )
}

parse_one_raw_igcaller_file <- function(path) {
  lines <- readLines(path, warn = FALSE)
  lines <- lines[str_detect(lines, "Translocation")]

  if (length(lines) == 0L) {
    return(tibble())
  }

  lines <- gsub("\\[|\\]", "", lines)
  lines <- gsub(";chr", "\tchr", lines)
  lines <- gsub(" - ", "\t", lines)
  lines <- gsub(":\\+", "\t\\+", lines)
  lines <- gsub(":-", "\t-", lines)

  parsed <- read.table(text = lines, fill = TRUE, stringsAsFactors = FALSE)
  if (ncol(parsed) < 15L) {
    stop("Raw IgCaller file has fewer than 15 parsed columns: ", path, call. = FALSE)
  }

  out <- as_tibble(parsed[, c(5, 6, 7, 8, 9, 10, 12, 15)])
  names(out) <- c(
    "breakpoint1", "breakpoint1_strand",
    "breakpoint2", "breakpoint2_strand",
    "gene1", "gene2", "IGCaller_Score", "Mappability_Issue"
  )

  out %>%
    mutate(
      Bam_File = gsub("_output_filtered\\.tsv$", ".bam", basename(path)),
      Sample = basename(path)
    )
}

parse_raw_igcaller_directory <- function(raw_dir) {
  if (!dir.exists(raw_dir)) {
    return(NULL)
  }

  raw_files <- list.files(
    raw_dir,
    pattern = "_output_filtered\\.tsv$|_filtered\\.tsv$",
    recursive = TRUE,
    full.names = TRUE
  )

  if (length(raw_files) == 0L) {
    return(NULL)
  }

  message("Parsing raw IgCaller filtered files from: ", normalizePath(raw_dir, winslash = "/", mustWork = TRUE))
  message("Raw IgCaller files found: ", length(raw_files))

  parsed_list <- lapply(raw_files, parse_one_raw_igcaller_file)
  parsed <- bind_rows(parsed_list)

  if (nrow(parsed) == 0L) {
    stop("Raw IgCaller files were found, but no Translocation rows were parsed.", call. = FALSE)
  }

  parsed
}

annotate_raw_igcaller_calls <- function(raw_calls, cytoband_file, metadata_csv = NULL) {
  cytobands <- read_cytoband_file(cytoband_file)

  breakpoint1 <- split_breakpoint(raw_calls$breakpoint1)
  breakpoint2 <- split_breakpoint(raw_calls$breakpoint2)
  break1_chromosome <- breakpoint1$chromosome
  break1_position <- breakpoint1$position
  break2_chromosome <- breakpoint2$chromosome
  break2_position <- breakpoint2$position

  annotated <- raw_calls %>%
    mutate(
      IGCaller_Score = as.numeric(IGCaller_Score),
      break1_chromosome = if_else(str_starts(.env$break1_chromosome, "chr"), .env$break1_chromosome, paste0("chr", .env$break1_chromosome)),
      break1_position_start = .env$break1_position,
      break1_position_end = break1_position_start,
      break2_chromosome = if_else(str_starts(.env$break2_chromosome, "chr"), .env$break2_chromosome, paste0("chr", .env$break2_chromosome)),
      break2_position_start = .env$break2_position,
      break2_position_end = break2_position_start
    )

  if (any(is.na(annotated$IGCaller_Score))) {
    stop("Raw IgCaller parsing produced NA IGCaller_Score values.", call. = FALSE)
  }
  if (any(is.na(annotated$break1_position_start) | is.na(annotated$break2_position_start))) {
    stop("Raw IgCaller parsing produced NA breakpoint positions.", call. = FALSE)
  }

  annotated <- annotated %>%
    add_potential_mm_translocation() %>%
    filter(Potential_MM_translocation == 1L) %>%
    filter(!(IGCaller_Score <= 20 & Mappability_Issue != "none")) %>%
    mutate(
      break1_cytoband = match_cytoband(break1_chromosome, break1_position_start, cytobands),
      break2_cytoband = match_cytoband(break2_chromosome, break2_position_start, cytobands),
      Recurrent_TRA = if_else(
        (str_detect(coalesce(break1_cytoband, ""), "11q13|4p16|16q23") & break2_cytoband == "chr14q32.33") |
          (str_detect(coalesce(break2_cytoband, ""), "11q13|4p16|16q23") & break1_cytoband == "chr14q32.33"),
        "Yes",
        "No"
      ),
      Sample = gsub("\\.fastq\\.gz$", "", Sample),
      trans_ID = paste(Sample, break1_cytoband, break2_cytoband),
      break1_cytoband = if_else(is.na(break1_cytoband), break1_chromosome, break1_cytoband),
      break2_cytoband = if_else(is.na(break2_cytoband), break2_chromosome, break2_cytoband),
      Translocation = paste(break1_cytoband, break2_cytoband, sep = "_"),
      Sorted_translocation = sort_translocation(Translocation),
      Common_MM_translocation = if_else(Sorted_translocation %in% myeloma_translocations, 1L, 0L)
    ) %>%
    add_potential_mm_translocation()

  if (!is.null(metadata_csv) && file.exists(metadata_csv)) {
    metadata <- read_csv(metadata_csv, show_col_types = FALSE) %>%
      mutate(
        Tumor_Sample_Barcode = Bam %>%
          str_remove_all("_PG|_WG") %>%
          str_replace_all("\\.filter.*|\\.ded.*|\\.recalibrate.*", ""),
        Bam_clean_tmp = gsub("\\.bam$", "", Bam)
      )
    annotated <- annotated %>% left_join(metadata, by = c("Bam_File" = "Bam"))
  } else {
    message("Metadata CSV not found; using Bam_File as Patient surrogate: ", metadata_csv)
  }

  if (!"Patient" %in% names(annotated)) {
    annotated$Patient <- annotated$Bam_File
  }
  annotated$Patient <- if_else(is.na(annotated$Patient), annotated$Bam_File, as.character(annotated$Patient))

  annotated
}

load_or_build_annotated_igcaller_calls <- function(config) {
  raw_calls <- parse_raw_igcaller_directory(config$raw_igcaller_dir)

  if (!is.null(raw_calls)) {
    annotated <- annotate_raw_igcaller_calls(
      raw_calls = raw_calls,
      cytoband_file = config$cytoband_file,
      metadata_csv = config$metadata_csv
    )
    write_tsv(
      annotated,
      file.path(config$output_dir, "igcaller_raw_parsed_annotated_mm_only_calls.tsv"),
      na = ""
    )
    saveRDS(
      annotated,
      file.path(config$output_dir, "igcaller_raw_parsed_annotated_mm_only_calls.rds")
    )
    return(annotated)
  }

  message("No raw IgCaller filtered files found in: ", config$raw_igcaller_dir)
  message("Falling back to annotated IgCaller RDS: ", config$annotated_igcaller_rds)
  stop_if_missing(config$annotated_igcaller_rds, "annotated IgCaller RDS")
  readRDS(config$annotated_igcaller_rds)
}

has_any_blacklist_overlap <- function(chrom, start, end, blacklist) {
  chrom <- if_else(str_starts(as.character(chrom), "chr"), as.character(chrom), paste0("chr", chrom))
  start <- as.numeric(start)
  end <- as.numeric(end)

  vapply(seq_along(chrom), function(i) {
    if (is.na(chrom[[i]]) || is.na(start[[i]]) || is.na(end[[i]])) {
      return(TRUE)
    }
    bed_chr <- blacklist[blacklist$chrom == chrom[[i]], , drop = FALSE]
    if (nrow(bed_chr) == 0L) {
      return(FALSE)
    }
    any(start[[i]] <= bed_chr$stop & end[[i]] >= bed_chr$start)
  }, logical(1))
}

apply_automated_filters <- function(calls, blacklist) {
  calls <- calls %>%
    mutate(
      IGCaller_Score = as.numeric(IGCaller_Score),
      Common_MM_translocation = as.integer(Common_MM_translocation),
      Potential_MM_translocation = as.integer(Potential_MM_translocation)
    ) %>%
    standardize_ig_partner()

  if (any(is.na(calls$IGCaller_Score))) {
    stop("IGCaller_Score contains NA after numeric conversion.", call. = FALSE)
  }

  threshold_filtered <- calls %>%
    filter(
      (Mappability_Issue != "none" & IGCaller_Score >= 100) |
        (Mappability_Issue == "none" & IGCaller_Score >= 50) |
        (Common_MM_translocation == 1L & IGCaller_Score > 15) |
        (Other_gene %in% relevant_myeloma_genes)
    ) %>%
    filter(Potential_MM_translocation == 1L | Other_gene %in% relevant_myeloma_genes)

  break1_blacklisted <- has_any_blacklist_overlap(
    threshold_filtered$break1_chromosome,
    threshold_filtered$break1_position_start,
    threshold_filtered$break1_position_end,
    blacklist
  )
  break2_blacklisted <- has_any_blacklist_overlap(
    threshold_filtered$break2_chromosome,
    threshold_filtered$break2_position_start,
    threshold_filtered$break2_position_end,
    blacklist
  )

  no_encode_blacklist <- threshold_filtered[!(break1_blacklisted | break2_blacklisted), , drop = FALSE]

  no_recurrent_artifacts <- no_encode_blacklist %>%
    filter(!(str_detect(Other_gene, "^(LOC|LINC)") & IGCaller_Score <= 200)) %>%
    group_by(IG_gene, Other_gene) %>%
    mutate(patient_count = n_distinct(Patient, na.rm = TRUE)) %>%
    ungroup() %>%
    filter(
      patient_count <= 2L |
        (Other_gene %in% key_myeloma_genes & Common_MM_translocation == 1L)
    )

  no_recurrent_artifacts %>%
    filter(!(Mappability_Issue != "none" & IGCaller_Score <= 100)) %>%
    filter(!(IGCaller_Score <= 20 & Other_gene %in% c("NSD2", "MAF"))) %>%
    filter(
      (Mappability_Issue == "none" & IGCaller_Score >= 50) |
        (Common_MM_translocation == 1L & IGCaller_Score >= 40) |
        (Other_gene %in% relevant_myeloma_genes) #AQSA| 
        #AQSA(Common_MM_translocation == 0L & IGCaller_Score >= 100) # <--- RESCUE HIGH-SCORE NON-CANONICAL CALLS
    ) %>%
    group_by(IG_gene, Other_gene) %>%
    mutate(patient_count = n_distinct(Patient, na.rm = TRUE)) %>%
    ungroup()
}

make_candidate_review_table <- function(filtered_calls) {
  out <- filtered_calls %>%
    filter(
      Common_MM_translocation == 1L #AQSA| 
        #AQSA(Common_MM_translocation == 0L & IGCaller_Score >= 100) # <--- ALLOWS HIGH-SCORE 0L CALLS
    )

  if ("timepoint_info" %in% names(out)) {
    out <- out %>% filter(timepoint_info %in% c("Baseline", "Diagnosis"))
  }

  out
}

make_final_cytoband_matrix <- function(confirmed_calls) {
  cyto_cols <- c(
    "chr11q13.2_chr14q32.33",
    "chr11q13.3_chr14q32.33",
    "chr14q32.33_chr4p16.3",
    "chr14q32.33_chr16q23.2",
    "chr14q32.33_chr8q24.21"
  )

  matrix <- confirmed_calls %>%
    filter(Common_MM_translocation == 1L) %>%
    group_by(Bam_File) %>%
    slice_max(order_by = IGCaller_Score, n = 1, with_ties = FALSE) %>%
    ungroup() %>%
    mutate(
      Sample = str_remove(Bam_File, "\\.bam$"),
      Sorted_translocation = if_else(
        str_starts(Sorted_translocation, "IGH"),
        sub("_.*", "", Sorted_translocation),
        Sorted_translocation
      )
    ) %>%
    select(Bam_File, Sample, Sorted_translocation) %>%
    distinct() %>%
    mutate(value = 1L) %>%
    tidyr::pivot_wider(
      names_from = Sorted_translocation,
      values_from = value,
      values_fill = 0L
    )

  for (col in cyto_cols) {
    if (!col %in% names(matrix)) {
      matrix[[col]] <- NA_integer_
    }
  }

  matrix %>%
    mutate(
      IGH_CCND1 = coalesce(
        .data[["chr11q13.2_chr14q32.33"]],
        .data[["chr11q13.3_chr14q32.33"]]
      )
    ) %>%
    transmute(
      Bam_File,
      Sample,
      IGH_CCND1,
      IGH_FGFR3 = .data[["chr14q32.33_chr4p16.3"]],
      IGH_MAF = .data[["chr14q32.33_chr16q23.2"]],
      IGH_MYC = .data[["chr14q32.33_chr8q24.21"]]
    )
}

write_qc_summary <- function(path, input_calls, filtered_calls, candidate_calls, confirmed_calls = NULL) {
  summary_lines <- c(
    paste("annotated_input_rows", nrow(input_calls), sep = "\t"),
    paste("automated_filtered_rows", nrow(filtered_calls), sep = "\t"),
    paste("candidate_common_mm_baseline_or_diagnosis_rows", nrow(candidate_calls), sep = "\t"),
    paste("automated_filtered_unique_patients", n_distinct(filtered_calls$Patient, na.rm = TRUE), sep = "\t"),
    paste("candidate_unique_patients", n_distinct(candidate_calls$Patient, na.rm = TRUE), sep = "\t")
  )

  if (!is.null(confirmed_calls)) {
    summary_lines <- c(
      summary_lines,
      paste("igv_confirmed_looks_real_eq_1_rows", nrow(confirmed_calls), sep = "\t"),
      paste("igv_confirmed_unique_patients", n_distinct(confirmed_calls$Patient, na.rm = TRUE), sep = "\t")
    )
  }

  writeLines(summary_lines, path)
}

stop_if_missing(config$blacklist_bed, "ENCODE blacklist BED")
dir.create(config$output_dir, recursive = TRUE, showWarnings = FALSE)

annotated_calls <- load_or_build_annotated_igcaller_calls(config)
validate_columns(annotated_calls, required_columns, "Annotated IgCaller table")

blacklist <- read_blacklist_bed(config$blacklist_bed)
automated_filtered_calls <- apply_automated_filters(annotated_calls, blacklist)
candidate_review_calls <- make_candidate_review_table(automated_filtered_calls)

write_tsv(
  automated_filtered_calls,
  file.path(config$output_dir, "igcaller_automated_extra_aggressive_calls.tsv"),
  na = ""
)
saveRDS(
  automated_filtered_calls,
  file.path(config$output_dir, "igcaller_automated_extra_aggressive_calls.rds")
)
write_tsv(
  candidate_review_calls,
  file.path(config$output_dir, "igcaller_candidate_common_mm_calls_for_igv_review.tsv"),
  na = ""
)

confirmed_calls <- NULL
if (file.exists(config$igv_review_xlsm)) {
  if (!requireNamespace("readxl", quietly = TRUE)) {
    stop("Package 'readxl' is required to read igv_review_xlsm: ", config$igv_review_xlsm, call. = FALSE)
  }

  igv_review <- readxl::read_excel(config$igv_review_xlsm)
  validate_columns(igv_review, c("Looks_real", "Bam_File", "IGCaller_Score", "Common_MM_translocation", "Sorted_translocation"), "IGV review workbook")

  confirmed_calls <- igv_review %>%
    mutate(
      Looks_real = as.numeric(Looks_real),
      IGCaller_Score = as.numeric(IGCaller_Score),
      Common_MM_translocation = as.integer(Common_MM_translocation)
    ) %>%
    filter(Looks_real == 1)

  evidence_override_samples <- igv_review %>%
    mutate(Looks_real = as.numeric(Looks_real)) %>%
    filter(Looks_real > 0.7) %>%
    select(any_of(c("Bam_clean_tmp", "Bam_File", "Patient", "Sample_ID", "Looks_real"))) %>%
    distinct()

  final_matrix <- make_final_cytoband_matrix(confirmed_calls)

  write_tsv(confirmed_calls, file.path(config$output_dir, "igcaller_igv_confirmed_calls.tsv"), na = "")
  write_tsv(evidence_override_samples, file.path(config$output_dir, "igcaller_evidence_override_samples_looks_real_gt_0_7.tsv"), na = "")
  write_tsv(final_matrix, file.path(config$output_dir, "translocation_data_cytoband_updated_simplified.tsv"), na = "")
  saveRDS(final_matrix, file.path(config$output_dir, "translocation_data_cytoband_updated_simplified.rds"))
} else {
  message("IGV review workbook not found; skipping final IGV-confirmed matrix: ", config$igv_review_xlsm)
}

write_qc_summary(
  file.path(config$output_dir, "igcaller_filter_qc_summary.tsv"),
  input_calls = annotated_calls,
  filtered_calls = automated_filtered_calls,
  candidate_calls = candidate_review_calls,
  confirmed_calls = confirmed_calls
)

message("Wrote simplified IgCaller outputs to: ", normalizePath(config$output_dir, winslash = "/", mustWork = TRUE))
message("Automated filtered calls: ", nrow(automated_filtered_calls))
message("Candidate common-MM calls for IGV review: ", nrow(candidate_review_calls))
if (!is.null(confirmed_calls)) {
  message("IGV-confirmed Looks_real == 1 calls: ", nrow(confirmed_calls))
}
