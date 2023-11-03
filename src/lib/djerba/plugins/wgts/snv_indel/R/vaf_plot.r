#! /usr/bin/env Rscript

# plotting code from https://github.com/oicr-gsi/djerba/blob/75149f1a2caefe25ba6ad5b9cc5f47b26f35a574/src/lib/djerba/R_markdown/html_report_default.Rmd#L512

library(dplyr)
library(ggplot2)
library(optparse)
library(scales)

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

# remove Silent and Splice_Region for consistency with the TMB count
MAF <- read.csv(maf_path, sep = "\t", header = TRUE, stringsAsFactors = FALSE) %>%
    filter(Variant_Classification != "Silent" & Variant_Classification != "Splice_Region") %>%
    select(-Chromosome) %>%
    inner_join(cytoBand) %>%
    mutate(OncoKB = ifelse(is.na(HIGHEST_LEVEL), ONCOGENIC, HIGHEST_LEVEL))

MAF$tumour_vaf_perc <- MAF$tumour_vaf * 100

options(bitmapType='cairo')
svg(out_path, width=7, height=1.5)

ggplot(MAF) + 
  geom_density(aes(x = tumour_vaf_perc), fill = "grey", alpha = 0.5,color="darkgrey") + 
  geom_point(aes(x = tumour_vaf_perc,y = 0), shape="|") + 

  scale_x_continuous( limit = c(0, 100)) + 
  scale_y_continuous(expand = c(0, 0),labels = percent) +
  
  xlab("Variant Allele Frequency (%)") +   ylab("% of mutations") +
  theme_classic() + 
  guides(fill='none')+
  theme(
    text = element_text(size = 10),
    panel.grid = element_blank(), 
    plot.margin = unit(c(10, 10, 10, 10), "points"),
    line = element_blank()
  ) 


dev.off()

txt <- paste(readLines(out_path), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)
