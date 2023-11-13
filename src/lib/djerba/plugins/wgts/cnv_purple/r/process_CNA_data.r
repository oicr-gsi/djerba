#! /usr/bin/env Rscript

rm(list=ls())
library(optparse)

# command line options
option_list = list(
  make_option(c("-d", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-g", "--genefile"), type="character", default=NULL, help="seg file", metavar="character"),
  make_option(c("-o", "--oncolist"), type="character", default=NULL, help="oncoKB cancer genes", metavar="character"),
  make_option(c("-p", "--ploidy"), type="character", default=NULL, help="sample ploidy for CN cutoffs", metavar="character")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

# set better variable names
outdir    <- opt$outdir
genefile  <- opt$genefile
oncolist  <- opt$oncolist
ploidy    <- as.numeric(opt$ploidy)

# source functions
basedir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), sep='/')
source(paste0(basedir, "/plugins/wgts/cnv_purple/r/CNA_supporting_functions.r"))

###################### CNA #####################

if (is.null(genefile)) {
  cat("No SEG file input, processing omitted\n")
} else {
  
  cat("Processing CNA data\n")
  
  oncogenes <- read.delim(oncolist, header=TRUE)
  raw_gene_data <- read.delim(genefile, header=TRUE) 
  
  CNAs <- preProcCNA(raw_gene_data, oncogenes, ploidy)
  
  # necessary file to find copy number profile of genes with small mutations
  write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[1]]), CNAs[[1]], check.names=FALSE),
              file=paste0(outdir, "/purple.data_CNA.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  
  # write the short data_CNA file (non-zero, oncoKB genes) for oncoKB annotator
  write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[2]]), CNAs[[2]], check.names=FALSE),
              file=paste0(outdir, "/purple.data_CNA_oncoKBgenes_nonDiploid.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  

}
