#! /usr/bin/env Rscript

# plotting code from https://github.com/oicr-gsi/djerba/blob/75149f1a2caefe25ba6ad5b9cc5f47b26f35a574/src/lib/djerba/R_markdown/html_report_default.Rmd#L497

library(dplyr)
library(ggplot2)
library(optparse)

option_list = list(
    make_option(c("-c", "--code"), type="character", default=NULL, help="TCGA code", metavar="character"),
    make_option(c("-o", "--output"), type="character", default=NULL, help="SVG output path", metavar="character"),
    make_option(c("-p", "--pga"), type="numeric", default=NULL, help="Percent Genome Altered", metavar="numeric")
)
# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
samplePGA <- opt$pga
sample_tcga <- opt$code
out_path <- opt$output

data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')
#external_pga_file <- paste(data_dir, 'pgacomp-externaldata.txt', sep='/')
#external_pga_data <- read.delim(external_pga_file, header = TRUE, stringsAsFactors = F)

#tcga_pga_file <- paste(data_dir, 'pgacomp-tcga.txt', sep='/')

tcga_pga_file <- 'clinical_PGA.txt'
tcga_pga_data <- read.table(tcga_pga_file, header = TRUE, stringsAsFactors = F,sep = "\t")

#subset external data to cancer type
#external_pga_data_type <- external_pga_data %>% filter(if (sample_tcga %in% external_pga_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)
#subset tcga data to cancer type
tcga_pga_data_type <- tcga_pga_data %>% filter(if (sample_tcga %in% tcga_pga_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)

options(bitmapType='cairo')

svg(out_path, width=8, height=2)
ggplot(tcga_pga_data, aes(x=PGA)) +
  geom_density(aes(fill = "All TCGA"), alpha = 0.5) + 
  scale_x_continuous(expand = c(0, 0), limit = c(0, max(samplePGA,  100))) +
 # scale_y_continuous(expand = c(0, 0)) +
  
  annotate(y = 0, yend=0.03, x=samplePGA, xend=samplePGA,geom="segment",linetype="solid",colour = "black") +
  annotate(geom="text",x = samplePGA,y=0,color="black",label="Sample PGA", hjust = -0.05, vjust = -11,size=3) +
  

  labs(x="percent genome altered",fill="TCGA Cohort") +
 # {
 #   if (sample_tcga %in% external_tmb_data_type$CANCER.TYPE)
 #     geom_density(data = external_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
 #   else if (sample_tcga %in% tcga_tmb_data_type$CANCER.TYPE)
 #     geom_density(data = tcga_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
 # } + scale_fill_discrete(name = "TMB Cohort") +
  
  theme_classic() +
  
  theme(
    legend.position = c(1, 0.8), 
    plot.margin = unit(c(2, 3, 0, 2), "lines"),
    axis.title.y=element_blank(),
    axis.text.y=element_blank(),
    axis.ticks.x=element_blank(),
    text = element_text(size = 10),
    panel.grid = element_blank(), 
    line = element_blank()
  ) 

dev.off()
