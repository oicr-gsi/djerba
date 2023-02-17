#! /usr/bin/env Rscript

# plotting code from https://github.com/oicr-gsi/djerba/blob/75149f1a2caefe25ba6ad5b9cc5f47b26f35a574/src/lib/djerba/R_markdown/html_report_default.Rmd#L497

library(dplyr)
library(ggplot2)
library(optparse)
library(scales)

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

label_location <- max(density(tcga_tmb_data$tmb)$y)
if(length(external_tmb_data_type$tmb) > 0){
  tmp_max <- max(density(external_tmb_data_type$tmb)$y)
  label_location <- max(label_location,tmp_max)
}
if(length(tcga_tmb_data_type$tmb) > 0){
  tmp_max <- max(density(tcga_tmb_data_type$tmb)$y)
  label_location <- max(label_location,tmp_max)
}

options(bitmapType='cairo')
svg(out_path, width=8, height=3)
ggplot(tcga_tmb_data, aes(tmb)) +
  geom_density(aes(fill = "All TCGA"), alpha = 0.5) + 
  scale_x_continuous(expand = c(0, 0), limit = c(0, max(sampleTMB, 25))) +
  scale_y_continuous(expand = c(0, 0),labels = percent) +
  coord_cartesian(xlim = c(0, max(sampleTMB, 25)),
                  clip = 'off') +
  
  geom_vline(xintercept = sampleTMB,linetype="solid",colour = "black")+
  geom_vline(xintercept = 10,linetype="longdash",colour = "red") +
  
  annotate(y=label_location,geom="text",x = sampleTMB, color="black",label="This tumour", hjust = -0.02,size=5,vjust=2) +
  annotate(y=label_location,geom="text",x = 10,color="red",label="TMB-H threshold", hjust =-0.02,size=5) +
  
  xlab("Coding Mutations per Mb") +
  ylab("% of samples") +
  {
    if (sample_tcga %in% external_tmb_data_type$CANCER.TYPE)
      geom_density(data = external_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
    else if (sample_tcga %in% tcga_tmb_data_type$CANCER.TYPE)
      geom_density(data = tcga_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
  } + scale_fill_discrete(name = "Cohort") +
  theme_classic() + 
  theme(text = element_text(size = 25),
        plot.margin = unit(c(1, 1, 1, 1), "lines"),
        panel.grid = element_blank(), 
        line = element_blank(),
        legend.background = element_rect(fill='transparent')
  )

dev.off()
