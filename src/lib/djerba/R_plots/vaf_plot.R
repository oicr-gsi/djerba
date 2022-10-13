#! /usr/bin/env Rscript

# plotting code from https://github.com/oicr-gsi/djerba/blob/75149f1a2caefe25ba6ad5b9cc5f47b26f35a574/src/lib/djerba/R_markdown/html_report_default.Rmd#L512

library(dplyr)
library(ggplot2)
library(optparse)

option_list = list(
    make_option(c("-d", "--dir"), type="character", default=NULL, help="Input report directory path", metavar="character"),
    make_option(c("-o", "--output"), type="character", default=NULL, help="SVG output path", metavar="character")
)
# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
maf_path <- paste(opt$dir, 'data_mutations_extended.txt', sep='/')
out_path <- opt$output

data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')
cytoBand <- read.csv((paste(data_dir, "cytoBand.txt", sep = "/")), sep = "\t", header = TRUE, stringsAsFactors = FALSE)

MAF <- read.csv(maf_path, sep = "\t", header = TRUE, stringsAsFactors = FALSE) %>%
    filter(Variant_Classification != "Silent" & Variant_Classification != "Splice_Region") %>%
    select(-Chromosome) %>%
    inner_join(cytoBand) %>%
    mutate(OncoKB = ifelse(is.na(Highest_level), oncogenic, Highest_level))

options(bitmapType='cairo')
svg(out_path, width=8, height=4)
ggplot(MAF) + 
  geom_density(aes(x = tumour_vaf), fill = "grey", alpha = 0.5) + 
  geom_rug(aes(x = tumour_vaf,y = 0), position = position_jitter(height = 0)) + 
  xlab("Variant Allele Frequency") + ylab("density") +
  theme_classic() + 
  theme(text = element_text(size = 15)) + 
  scale_x_continuous(expand = c(0,0), limit = c(0, 1)) + 
  scale_y_continuous(expand = c(0, 0)) + theme(plot.margin = unit(c(2, 3, 0, 2), "lines"))

dev.off()
