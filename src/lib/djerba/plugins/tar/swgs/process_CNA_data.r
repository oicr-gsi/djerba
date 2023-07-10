rm(list=ls())
library(CNTools)
library(optparse)
library(deconstructSigs)
library(BSgenome.Hsapiens.UCSC.hg38)

# command line options
option_list = list(
  make_option(c("-a", "--basedir"), type="character", default=NULL, help="cBioWrap base directory", metavar="character"),
  make_option(c("-f", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-c", "--segfile"), type="character", default=NULL, help="concatenated seg file", metavar="character"),
  make_option(c("-i", "--genebed"), type="character", default=NULL, help="gene bed for segmentation", metavar="character"),
  make_option(c("-k", "--oncolist"), type="character", default=NULL, help="oncoKB cancer genes", metavar="character")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE);
opt <- parse_args(opt_parser);

# set better variable names
basedir <- opt$basedir
outdir <- opt$outdir
segfile <- opt$segfile
genebed <- opt$genebed
oncolist <- opt$oncolist

# print options to output
print("Running singleSample with the following options:")
print(opt)

# source functions
source(paste0(basedir, "/convert_seg_to_gene_singlesample.r"))

###################### CNA #####################

print("Processing CNA data")
CNAs <- preProcCNA(segfile, genebed, oncolist)

print("writing seg file")
# segs
write.table(CNAs[[1]], file=paste0(outdir, "/data_segments.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# log2cna
print("writing log2 file")
write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[2]]), CNAs[[2]], check.names=FALSE),
  file=paste0(outdir, "/data_log2CNA.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# gistic-like file
print("writing cna file")
write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[3]]), CNAs[[3]], check.names=FALSE),
  file=paste0(outdir, "/data_CNA.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# write out the oncoKB genes
print("writing oncoKB genes")
write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[4]]), CNAs[[4]], check.names=FALSE),
  file=paste0(outdir, "/data_CNA_oncoKBgenes.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# write the truncated data_CNA file (non-zero, oncoKB genes) for oncoKB annotator
print("writing non-diploid oncoKB genes")
write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[5]]), CNAs[[5]], check.names=FALSE),
  file=paste0(outdir, "/data_CNA_oncoKBgenes_nonDiploid.txt"), sep="\t", row.names=FALSE, quote=FALSE)
