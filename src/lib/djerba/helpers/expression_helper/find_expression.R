#! /usr/bin/env Rscript

# find RNASeq expression
# adapted from singleSample.R

library(optparse)

gepfile <- opt$gepfile
outdir <- opt$outdir
enscon <- opt$enscon
genelist <- opt$genelist

option_list = list(
  make_option(c("-e", "--enscon"), type="character", default=NULL, help="ensemble conversion file", metavar="character"),
  make_option(c("-g", "--gepfile"), type="character", default=NULL, help="concatenated gep file", metavar="character"),
  make_option(c("-l", "--genelist"), type="character", default=NULL, help="subset cnas and rnaseq to these", metavar="character"),
  make_option(c("-o", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-t", "--tcgadata"), type="character", default=NULL, help="tcga datadir", metavar="character"),
  make_option(c("-c", "--tcgacode"), type="character", default=NULL, help="tcga code", metavar="character"),

)
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
enscon <- opt$enscon
genelist <- opt$genelist
gepfile <- opt$gepfile
outdir <- opt$outdir
tcgadata <- opt$tcgadata
tcgacode <- opt$tcgacode


if length(Filter(is.null, c(enscon, genelist, gepfile, outdir, tcgadata, tcgacode))) > 0 {
    print("ERROR: Missing inputs for find_expression.R")
    quit(status=1)
} else {
  print("Processing RNASEQ data")

  # preprocess the full data frame
  df <- preProcRNA(gepfile, enscon, genelist)
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
  load(file=paste(tcgadata, "/", tcgacode,".PANCAN.matrix.rdf", sep=""))
  df_tcga <- get(tcgacode)

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
