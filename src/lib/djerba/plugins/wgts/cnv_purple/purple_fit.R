
library(optparse)

option_list = list(
  make_option(c("-d", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-r", "--range_file"), type="character", default=NULL, help="purity range file", metavar="character"),
  make_option(c("-c", "--cairo"), type="boolean", default=TRUE, help="enable cairo mode", metavar="boolean")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
argv <- parse_args(opt_parser)

plotDir   <- argv$outdir
range_file <- argv$range_file

if(isTRUE(argv$cairo)){
  local_bitmapType <- "cairo"
}else{
  local_bitmapType <- getOption("bitmapType")
}

rangeDF = read.table(file = range_file, sep = "\t", header = T, comment.char = "!") 

plot_purity_range(rangeDF)