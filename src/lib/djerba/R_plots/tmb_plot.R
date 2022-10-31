#! /usr/bin/env Rscript

# plotting code from https://github.com/oicr-gsi/djerba/blob/75149f1a2caefe25ba6ad5b9cc5f47b26f35a574/src/lib/djerba/R_markdown/html_report_default.Rmd#L497

library(dplyr)
library(ggplot2)
library(optparse)

option_list = list(
    make_option(c("-c", "--code"), type="character", default=NULL, help="TCGA code", metavar="character"),
    make_option(c("-o", "--output"), type="character", default=NULL, help="SVG output path", metavar="character"),
    make_option(c("-t", "--tmb"), type="numeric", default=NULL, help="TMB per Mb", metavar="numeric")
)
# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
sampleTMB <- opt$tmb
sample_tcga <- opt$code
out_path <- opt$output

data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')
external_tmb_file <- paste(data_dir, 'tmbcomp-externaldata.txt', sep='/')
external_tmb_data <- read.delim(external_tmb_file, header = TRUE, stringsAsFactors = F)
tcga_tmb_file <- paste(data_dir, 'tmbcomp-tcga.txt', sep='/')
tcga_tmb_data <- read.delim(tcga_tmb_file, header = TRUE, stringsAsFactors = F)

#subset external data to cancer type
external_tmb_data_type <- external_tmb_data %>% filter(if (sample_tcga %in% external_tmb_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)
#subset tcga data to cancer type
tcga_tmb_data_type <- tcga_tmb_data %>% filter(if (sample_tcga %in% tcga_tmb_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)

options(bitmapType='cairo')
svg(out_path, width=8, height=4)
ggplot(tcga_tmb_data, aes(tmb)) +
  geom_density(aes(fill = "All TCGA"), alpha = 0.5) + 
  scale_x_continuous(expand = c(0, 0), limit = c(0, max(sampleTMB, 25))) +
  scale_y_continuous(expand = c(0, 0)) +
  coord_cartesian(xlim = c(0, max(sampleTMB, 25)),
                  clip = 'off') +
  annotate(y = 0, yend=0.25, x=sampleTMB, xend=sampleTMB,geom="segment",linetype="solid",colour = "black") +
  annotate(geom="text",x = sampleTMB,y=0,color="black",label="Sample TMB", hjust = 0.5, vjust = -30) +
  annotate(y = 0, yend=0.25, x=10, xend=10,geom="segment",linetype="longdash",colour = "red") +
  annotate(geom="text",x = 10,y=0,color="red",label="TMB-H", hjust = 0.3, vjust = -30) +
  xlab("Coding Mutations per Mb") +
  ylab("density") +
  {
    if (sample_tcga %in% external_tmb_data_type$CANCER.TYPE)
      geom_density(data = external_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
    else if (sample_tcga %in% tcga_tmb_data_type$CANCER.TYPE)
      geom_density(data = tcga_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
  } + scale_fill_discrete(name = "Cohort") +
  theme_classic() + 
  theme(text = element_text(size = 15),
        legend.position = c(0.9, 0.9),
        plot.margin = unit(c(2, 3, 0, 2), "lines"))

dev.off()
