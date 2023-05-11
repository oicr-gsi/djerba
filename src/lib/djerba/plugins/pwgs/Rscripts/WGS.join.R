#! /usr/bin/env Rscript

library(tidyr)
library(data.table)
library(dplyr)
library(optparse)

option_list = list(
  make_option(c("-i", "--wgs_input"), type="character", default=NULL, help="input directory", metavar="character"),
  make_option(c("-v", "--vaf_results"), type="character", default=NULL, help="vaf", metavar="character"),
  make_option(c("-g", "--groupid"), type="character", default=NULL, help="group id ", metavar="character"),
  make_option(c("-o", "--output_directory"), type="character", default=NULL, help="output directory", metavar="character")
) 

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE);
opt <- parse_args(opt_parser)

# set variable
djerba_directory <- opt$wgs_input
plasma_vaf <- opt$vaf_results
group_id <- opt$groupid
out_directory <- opt$output_directory

primary <- fread(djerba_directory)
plasma <- fread(plasma_vaf)

plasma<- separate(plasma, col = locus,into = c("Chromosome","Start_Position"),sep = "-")
plasma$Start_Position <- as.numeric(plasma$Start_Position)
plasma_join <- inner_join(plasma,primary)

if(nrow(plasma_join) > 0 ){
  plasma_join$whizbam_plasma <- paste0(plasma_join$whizbam,"&project3=PWGVAL&library3=",group_id,"&file3=",group_id,".bam&seqtype3=GENOME")
  
  plasma_join$impact <-  factor(plasma_join$IMPACT, levels = c("HIGH","MODERATE","MODIFIER" ,"LOW"))
  
  plasma_sort <- plasma_join %>%
    select(Chromosome,Start_Position,Reference_Allele,Tumor_Seq_Allele2,goodreads,detectedsites,vaf,Hugo_Symbol,Variant_Classification,BIOTYPE,impact,Consequence,SIFT,PolyPhen,CLIN_SIG,GENE_IN_ONCOKB,ONCOGENIC,HGVSp_Short,dbSNP_RS,whizbam_plasma) %>%
   arrange(ONCOGENIC,-GENE_IN_ONCOKB,impact,SIFT,PolyPhen,CLIN_SIG,BIOTYPE,Variant_Classification,Consequence)
} else {
  plasma_sort <- plasma_join
}

write.table(
  plasma_sort,
  file = paste0(out_directory,"/data_mutations_extended","_plasma",".txt"),
  append = F, quote = FALSE, sep = "\t", 
  eol = "\n", na = "NA",dec = ".", 
  row.names = FALSE,  col.names = TRUE
)
