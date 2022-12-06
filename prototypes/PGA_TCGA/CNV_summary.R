
library(optparse)

option_list = list(
  make_option(c("-f", "--file"), type="character", default=NULL, help="input file", metavar="character")
)
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
input_file <- opt$file

seg <- read.table(input_file,header = T)

seg$seg_length <- as.numeric(seg$End) - as.numeric(seg$Start)
seg_changed <- seg[seg$Copy_Number != 2,]
PGA <- round(sum(seg_changed$seg_length) / sum(seg$seg_length) * 100,2)

noquote(c(unique(seg_changed$GDC_Aliquot),PGA))
