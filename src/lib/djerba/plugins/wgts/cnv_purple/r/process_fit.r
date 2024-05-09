#! /usr/bin/env Rscript

library(optparse)

options(bitmapType='cairo')
basedir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), sep='/')
source(paste0(basedir, "/plugins/wgts/cnv_purple/r/purple_QC_functions.r"))

option_list = list(
  make_option(c("-d", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-r", "--range_file"), type="character", default=NULL, help="purity range file", metavar="character")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
argv <- parse_args(opt_parser)

dir_path   <- argv$outdir
range_file <- argv$range_file

rangeDF = read.table(file = range_file, sep = "\t", header = T, comment.char = "!") 

purity_plot <- plot_purity_range(rangeDF)

svg(paste0(dir_path,"/purple.range.svg"), width = 8, height = 7)
print(purity_plot)
dev.off()


