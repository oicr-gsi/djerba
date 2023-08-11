
rm(list=ls())
library(CNTools)
library(optparse)
library(BSgenome.Hsapiens.UCSC.hg38)

# command line options
option_list = list(
  make_option(c("-a", "--basedir"), type="character", default=NULL, help="R scripts directory", metavar="character"),
  make_option(c("-f", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  
  make_option(c("-c", "--segfile"), type="character", default=NULL, help="concatenated seg file", metavar="character"),
  make_option(c("-e", "--gepfile"), type="character", default=NULL, help="concatenated gep file", metavar="character"),
  make_option(c("-b", "--maffile"), type="character", default=NULL, help="concatenated maf file", metavar="character"),
  
  make_option(c("-n", "--tcgadata"), type="character", default=NULL, help="tcga datadir", metavar="character"),
  make_option(c("-i", "--genebed"), type="character", default=NULL, help="gene bed for segmentation", metavar="character"),
  make_option(c("-k", "--oncolist"), type="character", default=NULL, help="oncoKB cancer genes", metavar="character"),
  make_option(c("-g", "--enscon"), type="character", default=NULL, help="ensemble conversion file", metavar="character"),
  make_option(c("-u", "--whizbam_url"), type="character", default="https://whizbam.oicr.on.ca", help="whizbam url", metavar="character"),
  
  make_option(c("-o", "--tcgacode"), type="character", default=NULL, help="tcga code", metavar="character"),
  make_option(c("-T", "--tar"), type="character", default=FALSE, help="true or false value for tar assay", metavar="boolean")

)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

# set better variable names
basedir <- opt$basedir
outdir <- opt$outdir
segfile <- opt$segfile
genebed <- opt$genebed
oncolist <- opt$oncolist
enscon <- opt$enscon
tcgadata <- opt$tcgadata
tcgacode <- opt$tcgacode
maffile <- opt$maffile
whizbam_url <- opt$whizbam_url
gepfile <- opt$gepfile
tar <- opt$tar

source(paste0(basedir, "supporting_functions.r"))

###################### CNA #####################

if (is.null(segfile)) {
   print("No SEG file input, processing omitted")
} else {
  
  print("Processing CNA data")
  cutoffs <- log_r_cutoff_finder(purity)
  CNAs <- preProcCNA(segfile, genebed, cutoffs, oncolist)
  
  print("writing seg file")
  # segs
  write.table(CNAs[[1]], file=paste0(outdir, "/data.seg"), sep="\t", row.names=FALSE, quote=FALSE)
  
  # log2cna
  print("writing log2 file")
  write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[2]]), CNAs[[2]], check.names=FALSE),
    file=paste0(outdir, "/data_log2CNA.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  
  # write the truncated data_CNA file (non-zero, oncoKB genes) for oncoKB annotator
  print("writing non-diploid oncoKB genes")
  write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[5]]), CNAs[[5]], check.names=FALSE),
    file=paste0(outdir, "/data_CNA_oncoKBgenes_nonDiploid.txt"), sep="\t", row.names=FALSE, quote=FALSE)

}
  
###################### VEP #####################

if (is.null(maffile)) {
  print("No MAF file input, processing omitted")
  } else {
  print("Processing Mutation data")
  
  # annotate with filters
  print("--- reading MAF data ---")
  maf_df <- read.csv(maffile, sep="\t", header=TRUE, check.names=FALSE, stringsAsFactors=FALSE)
  
  df_filter <- procVEP(maf_df)
  
  # add whizbam links
  df_filt_whizbam <- construct_whizbam_links(df_filter, whizbam_url)
  
  # get pass
  write.table(df_filt_whizbam, file=paste0(outdir, "/data_mutations_extended.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  
  if ( dim(df_filt_whizbam)[[1]] == 0 ) {
    print("No passed mutations")
    write.table(df_filt_whizbam, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  } else {
    # subset to oncokb annotated genes
    df_filt_oncokb <- subset(df_filt_whizbam, ONCOGENIC == "Oncogenic" | ONCOGENIC == "Likely Oncogenic")
    
    if ( dim(df_filt_oncokb)[[1]] == 0 ) {print("no oncogenic mutations")} 
    write.table(df_filt_oncokb, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  }
}

#################### RNASEQ Expression ####################

if (is.null(gepfile)) {	
  print("No RNASEQ input, processing omitted") 
} else {
  print("Processing RNASEQ data")
 
  # preprocess the full data frame
  df <- preProcRNA(gepfile, enscon)
  sample <- colnames(df)[1]

  # calculate z-score and percentiles TGL
  df_zscore <- compZ(df)
  df_percentile <- data.frame(signif(pnorm(as.matrix(df_zscore)), digits=4), check.names=FALSE)

  # write zscores
  write.table(data.frame(Hugo_Symbol=rownames(df_zscore), df_zscore, check.names=FALSE),
    file=paste0(outdir, "/data_expression_zscores_comparison.txt"), sep="\t", row.names=FALSE, quote=FALSE)

  # write percentiles
  write.table(data.frame(Hugo_Symbol=rownames(df_percentile), df_percentile, check.names=FALSE),
    file=paste0(outdir, "/data_expression_percentile_comparison.txt"), sep="\t", row.names=FALSE, quote=FALSE)

  print("getting TCGA-level data")

  # get TCGA comparitor
  load(file=paste(tcgadata, "/", tcgacode,".PANCAN.matrix.rdf", sep=""))
  df_tcga <- get(tcgacode)

  # equalize dfs (get common genes)
  df_stud_tcga <- get_common_genes(df, df_tcga)
  
  df_zscore <- compZ(df_stud_tcga)
  df_zscore_sample <- data.frame(Hugo_Symbol=rownames(df_zscore), df_zscore[,1], check.names=FALSE)
  df_percentile <- data.frame(signif(pnorm(as.matrix(df_zscore)), digits=4), check.names=FALSE)

  # z-score TCGA
  write.table(data.frame(Hugo_Symbol=rownames(df_zscore), df_zscore[sample], check.names=FALSE),
    file=paste0(outdir, "/data_expression_zscores_tcga.txt"), sep="\t", row.names=FALSE, quote=FALSE)

  # percentile TCGA
  write.table(data.frame(Hugo_Symbol=rownames(df_percentile), df_percentile[sample], check.names=FALSE),
    file=paste0(outdir, "/data_expression_percentile_tcga.txt"), sep="\t", row.names=FALSE, quote=FALSE)
}
