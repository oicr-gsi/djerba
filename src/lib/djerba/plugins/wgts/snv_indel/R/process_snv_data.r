
rm(list=ls())
library(optparse)
library(BSgenome.Hsapiens.UCSC.hg38)

# command line options
option_list = list(
  make_option(c("-a", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-b", "--basedir"), type="character", default=NULL, help="R scripts directory", metavar="character"),
  
  make_option(c("-e", "--maffile"), type="character", default=NULL, help="concatenated maf file", metavar="character"),
  
  make_option(c("-h", "--enscon"), type="character", default=NULL, help="ensemble conversion file", metavar="character"),
  make_option(c("-i", "--whizbam_url"), type="character", default="https://whizbam.oicr.on.ca", help="whizbam url", metavar="character"),

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

# set better variable names
basedir <- opt$basedir
outdir <- opt$outdir
enscon <- opt$enscon
maffile <- opt$maffile
whizbam_url <- opt$whizbam_url

source(paste0(basedir, "/R/supporting_functions.r"))


###################### VEP #####################

if (is.null(maffile)) {
  print("No MAF file input, processing omitted")
  } else {
  print("Processing Mutation data")
  
  # annotate with filters
  print("--- reading MAF data ---")
  maf_df <- read.csv(maffile, sep="\t", header=TRUE, check.names=FALSE, stringsAsFactors=FALSE)
  
  df_filter <- procVEP(maf_df)
  df_filt_whizbam <- construct_whizbam_links(df_filter, whizbam_url)
  
  write.table(df_filt_whizbam, file=paste0(outdir, "/data_mutations_extended.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  
  if ( dim(df_filter)[[1]] == 0 ) {
    print("No passed mutations")
    write.table(df_filt_whizbam, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  } else {
    # subset to oncokb annotated genes
    df_filt_oncokb <- subset(df_filt_whizbam, ONCOGENIC == "Oncogenic" | ONCOGENIC == "Likely Oncogenic")
    
    if ( dim(df_filt_oncokb)[[1]] == 0 ) {
      print("no oncogenic mutations")
      } 
    write.table(df_filt_oncokb, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  }
}
