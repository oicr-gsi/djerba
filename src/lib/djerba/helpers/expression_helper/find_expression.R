#! /usr/bin/env Rscript

# find RNASeq expression
# adapted from singleSample.R

library(optparse)

# functions originally from convert_rsem_results_zscore.r

# preprocess function
preProcRNA <- function(gepfile, enscon){

 # read in data
 gepData <- read.csv(gepfile, sep="\t", header=TRUE, check.names=FALSE)
 ensConv <- read.csv(enscon, sep="\t", header=FALSE)

 # rename columns
 colnames(ensConv) <- c("gene_id", "Hugo_Symbol")

 # merge in Hugo's, re-order columns, deduplicate
 df <- merge(x=gepData, y=ensConv, by="gene_id", all.x=TRUE)
 df <- subset(df[,c(ncol(df),2:(ncol(df)-1))], !duplicated(df[,c(ncol(df),2:(ncol(df)-1))][,1]))
 df <- df[!is.na(df$Hugo_Symbol),]
 row.names(df) <- df[,1]
 df <- df[,-1]

 # return the data frame
 return(df)
}

# simple zscore function
compZ <- function(df) {

 # scale row-wise
 df_zscore <- t(scale(t(df)))

 # NaN (when SD is 0) becomes 0
 df_zscore[is.nan(df_zscore)] <- 0

 # we want a dataframe
 df_zscore <- data.frame(signif(df_zscore, digits=4), check.names=FALSE)

 return(df_zscore)
}

option_list = list(
  make_option(c("-e", "--enscon"), type="character", default=NULL, help="ensemble conversion file", metavar="character"),
  make_option(c("-g", "--gepfile"), type="character", default=NULL, help="concatenated gep file", metavar="character"),
  make_option(c("-o", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-t", "--tcgadata"), type="character", default=NULL, help="tcga datadir", metavar="character"),
  make_option(c("-c", "--tcgacode"), type="character", default=NULL, help="tcga code", metavar="character")
)
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
enscon <- opt$enscon
gepfile <- opt$gepfile
outdir <- opt$outdir
tcgadata <- opt$tcgadata
tcgacode <- opt$tcgacode

if (is.null(enscon) |  is.null(gepfile) | is.null(outdir) | is.null(tcgadata) | is.null(tcgacode)) {
    print("ERROR: Missing inputs for find_expression.R")
    quit(status=1)
} else {
  print("Processing RNASEQ data")

  # preprocess the full data frame
  df <- preProcRNA(gepfile, enscon)
  sample <- colnames(df)[1]

  print("getting CAP-level data")
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
#  load(file=paste(tcgadata, "/", tcgacode,".PANCAN.matrix.rdf", sep=""))
#  df_tcga <- get(tcgacode)


  # get TCGA comparator
  file_path <- paste(tcgadata, "/", tcgacode, ".PANCAN.matrix.rdf", sep="")
  if (file.exists(file_path)) {
      load(file=file_path)
      df_tcga <- get(tcgacode)
} else {
      # default to TCGA_ALL_TUMOR if the file doesn't exist
      print("Could not find RODiC data with given oncotree code. Defaulting to TCGA_ALL_TUMOR.PANCAN.matrix.rdf")
      load(file=paste(tcgadata, "/TCGA_ALL_TUMOR.PANCAN.matrix.rdf", sep=""))
      df_tcga <- get("TCGA_ALL_TUMOR")
}


  # equalize dfs (get common genes)
  comg <- as.character(intersect(row.names(df_tcga), row.names(df)))
  df_tcga_common <- df_tcga[row.names(df_tcga) %in% comg, ]
  df_tcga_common_sort <- df_tcga_common[ order(row.names(df_tcga_common)), ]
  df_stud_common <- df[row.names(df) %in% comg, ]
  df_stud_common_sort <- df_stud_common[ order(row.names(df_stud_common)), ]
  df_stud_tcga <- merge(df_stud_common_sort, df_tcga_common_sort, by=0, all=TRUE)
  df_stud_tcga[is.na(df_stud_tcga)] <- 0
  rownames(df_stud_tcga) <- df_stud_tcga$Row.names
  df_stud_tcga$Row.names <- NULL
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
