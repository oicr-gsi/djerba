#!/usr/bin/Rscript
# For running on gphost01/02

# Author: Emma Titmuss, etitmuss@bcgsc.ca
# Date: June 2022 (CAPTIV8 V3.0) R version
# This script is to generate a score for enrolling patients with WGTA to the CAPTIV-8 trial.
# A score above 5 is eligible for the trial as of this version (V3.0).

# To run, provide a tab delimited meta file with the following parameters:

# Patient ID 
# DNA_RNA Library IDs or biop1 / 2 / other identifier
# Path / to / RICO / immunedeconv / CIBERSORT / results / txt file
# Path / to / RICO / RSEM / expression / txt file
# Path / to / TMBur / "TMB_counts" file OR TMB value for genomic SNVs and indels e.g. 10.16
# SWISNF alterations "yes / no" - see README for alteration requirement
# Colorectal sample "yes / no"
# Lymph related cancer / biopsy "yes / no"
# Presence of virus "yes / no"
#
# -m / path / to / meta file
# To run: ./CAPTIV8_external_v3.R -m /path/to/meta/file

#--------------------------------------------------------
# LOAD PACKAGES
#--------------------------------------------------------

library(plyr)
library(dplyr)
library(optparse)
library(ggplot2)
library(CMSclassifier)

#--------------------------------------------------------
# SET ARGUMENTS
#--------------------------------------------------------
option_list = list(
    make_option(c("-m", "--meta"), type="character", default=NULL, help="POG case", metavar="character"),
    make_option(c("-o", "--outdir"), type="character", default=NULL, help="Output directory", metavar="character"),
    make_option(c("-b", "--bed"), type="character", default=NULL, help="Bed file path", metavar="character")
); 

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

if (is.null(opt$meta)){
  print_help(opt_parser)
  stop("Please provide a meta file (-m)! See README for formatting.", call.=FALSE)
}

meta_path <- opt$meta
bed_file <- opt$bed
outdir <- opt$outdir

version <- "version 3.0"

#--------------------------------------------------------
# Pulling in meta data
#--------------------------------------------------------

meta_file <- read.delim(meta_path, header=FALSE, sep='\t')

patient <- meta_file[1,2]
libraries <- meta_file[2,2]
cibersort <- meta_file[3,2]
rsem <- meta_file[4,2]
tmb <- as.numeric(meta_file[5,2])
swisnf <- meta_file[6,2]
colon <- meta_file[7,2]
lymph <- meta_file[8,2]
virus <- meta_file[9,2]

print(paste0("Running CAPTIV-8 score for ", patient, ": ", libraries))
print(paste0("Lymph related sample: ", lymph))
print("Grabbing files...")

# Add logic for rejecting incorrect yes / nos for variables

#--------------------------------------------------------
# Mutation burden
#--------------------------------------------------------

print(paste0("Mutation burden: ", tmb))
print(" ")

#--------------------------------------------------------
# Expression analysis
#--------------------------------------------------------

#-------------------------------------------------------------------------- M1M2 scoring

exp <- read.delim(rsem, header=TRUE, sep='\t')

exp$gene_id_simple <- sub("\\.\\d+$", "", exp$gene_id)

M1M2_genes <- c("ENSG00000131203", "ENSG00000078081", "ENSG00000169245", "ENSG00000169248", "ENSG00000221963","ENSG00000138755", 
                "ENSG00000144837", "ENSG00000050730", "ENSG00000172724", "ENSG00000126353")

m1m2_exp <- subset(exp, exp$gene_id_simple %in% M1M2_genes)
m1m2 <- mean(m1m2_exp$TPM)

print(paste0("M1M2 expression: ", m1m2))
print(" ")

#-------------------------------------------------------------------------- CMS Subtyping for CRCs

if (colon %in% c("yes", "Yes", "YES", "y", "Y")){
  print("Running CMS subtyping for colorectal cancer...")

  Gene.names.file <- bed_file
  
  Gene.names <- read.table(Gene.names.file, sep='\t',header=TRUE)
  
  exp$entrezgene_id <- Gene.names$Entrez_ID[match(exp$gene_id, Gene.names$Ensembl_ID)]
  
  cms_input <- subset(exp, select=c("entrezgene_id", "TPM"))

  cms_input <- subset(cms_input, !is.na(entrezgene_id))
  cms_input$TPM <- log(cms_input$TPM +1)
  cms_input <- cms_input[!duplicated(cms_input$entrezgene_id),]

  row.names(cms_input) <- cms_input[,1]
  cms_input[,1] <- NULL
  cms_input$dup <- cms_input[,1] #it seems like classifyCMS.SSP needs at least two samples/columns to run, so duplicate the values
  
  cms_res <- classifyCMS.SSP(cms_input) # classify sample
#  cms_res <- data.frame(sample_id = row.names(cms_res), nearestCMS = cms_res$RF.nearestCMS, predictedCMS = cms_res$RF.predictedCMS)
#  paste(head(cms_res))

  #write.table(cms_res[1,], paste0("CMS_subtyping_", patient, "_", libraries, ".txt"), quote=FALSE, sep="\t", row.names=FALSE, col.names=TRUE)
  print(paste0("CMS subtype: ", cms_res$SSP.nearestCMS[1]))
} else {
  print("No CMS subtyping required")
}
print(" ")

#--------------------------------------------------------
# Immune scoring
#--------------------------------------------------------

cibersort_df <- read.csv(cibersort, sep=',', header=TRUE, comment.char="#")
cd8 <- subset(cibersort_df, cibersort_df[1] == "T cell CD8+")[,2]
print(paste0("CD8+ T cell score: ", cd8))
print(" ")
#cms_evidence <- "yes"

#--------------------------------------------------------
# Scoring
#--------------------------------------------------------

print("Generating score...")
print(" ")

cd8_score <- case_when(lymph == "yes" && cd8 >= 1.15 ~ 4,
                       lymph == "no" && cd8 >= 0.59 ~ 6,
                       lymph == "yes" && cd8 >= 0.37 ~ 2,
                       lymph == "no" && cd8 >= 0.24 ~ 4,
                       lymph == "no" && cd8 >= 0.09 ~ 2,
                       TRUE ~ 0)

m1m2_score <- case_when(lymph == "no" && m1m2 >= 41.29 ~ 3,
                       lymph == "yes" && m1m2 >= 54.63 ~ 2,
                       lymph == "no" && m1m2 >= 22.84 ~ 2,
                       lymph == "no" && m1m2 >= 6.96 ~ 1,
                       TRUE ~ 0)

cms_score <- case_when(colon == "yes" && cms_res$SSP.nearestCMS[1] == "CMS1" ~ 3, 
                       TRUE ~ 0)

tmb_score <- case_when(tmb >= 20 ~ 6, 
                       tmb >= 10 ~ 4,
                       tmb >= 8 ~ 2,
                       TRUE ~ 0)

virus_score <- case_when(virus == "yes" ~ 3,
                       TRUE ~ 0)

swisnf_score <- case_when(swisnf == "yes" ~ 3,
                       TRUE ~ 0)

orig_captiv8_score <- cd8_score + m1m2_score + swisnf_score + tmb_score + virus_score + cms_score

captiv8_score <- ifelse(orig_captiv8_score > 0, orig_captiv8_score - 1, orig_captiv8_score) # addressing fixed 5 threshold
eligible <- ifelse(captiv8_score >= 5, "Eligible", "Not eligible")

print(paste0("Patient is:  ", eligible))
print(paste0("Score:  ", captiv8_score))

# Scaling individual scores for reporting to match the scaled 5 threshold
cd8_score <-  (cd8_score / orig_captiv8_score) * captiv8_score
m1m2_score <-  (m1m2_score / orig_captiv8_score) * captiv8_score
swisnf_score <-  (swisnf_score / orig_captiv8_score) * captiv8_score
tmb_score <-  (tmb_score / orig_captiv8_score) * captiv8_score
virus_score <-  (virus_score / orig_captiv8_score) * captiv8_score
cms_score <-  (cms_score / orig_captiv8_score) * captiv8_score

print("")
print("Writing output file... ")
print("...")

marker <- c("CD8+", "M1M2", "SWISNF", "TMB", "Viral", "CMS", "Lymph node", "CAPTIV-8 score", "Eligibility")
score <- c(cd8_score, m1m2_score, swisnf_score, tmb_score, virus_score, cms_score, lymph, captiv8_score, eligible)
evidence <- c(cd8, m1m2, swisnf, tmb, virus, cms_evidence, lymph, version, captiv8_score)

output_file <- data.frame(marker, score, evidence)

write.table(output_file, paste0("CAPTIV8_", patient, "_", libraries, ".txt"), row.names =FALSE, quote=FALSE, sep='\t')

print(output_file)
