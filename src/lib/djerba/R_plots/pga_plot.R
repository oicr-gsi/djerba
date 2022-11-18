#! /usr/bin/env Rscript

library(dplyr)
library(ggplot2)
library(optparse)

option_list = list(
    make_option(c("-o", "--output"), type="character", default=NULL, help="SVG output path", metavar="character"),
    make_option(c("-p", "--pga"), type="numeric", default=NULL, help="Percent Genome Altered", metavar="numeric")
    #  make_option(c("-c", "--code"), type="character", default=NULL, help="TCGA code", metavar="character"),
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

samplePGA <- as.numeric(opt$pga)
out_path <- opt$output
#sample_tcga <- opt$code

data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')
tcga_pga_file <- paste(data_dir, 'pgacomp-tcga.txt', sep='/')
tcga_pga_data <- read.table(tcga_pga_file, header = TRUE, stringsAsFactors = F,sep = "\t")

#subset tcga data to cancer type
#tcga_pga_data_type <- tcga_pga_data %>% filter(if (sample_tcga %in% tcga_pga_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)

options(bitmapType='cairo')

svg(out_path, width=8, height=3)
ggplot(tcga_pga_data, aes(x=PGA)) +
  geom_density(aes(fill = "All TCGA"), alpha = 0.5) + 
  scale_x_continuous(expand = c(0, 0), limit = c(0, max(samplePGA,  100))) +
 # scale_y_continuous(expand = c(0, 0)) +
  
  geom_vline(xintercept = samplePGA,linetype="solid",colour = "black")+
#  annotate(y = 0, yend=0.03, x=samplePGA, xend=samplePGA,geom="segment",linetype="solid",colour = "black") +
  annotate(geom="text",x = samplePGA,y=0,color="black",label="This tumour", hjust = 0.3, vjust = -25.3) +


  labs(x="percent genome altered",fill="Cohort",y="% of samples") +
 # {
 #   if (sample_tcga %in% external_tmb_data_type$CANCER.TYPE)
 #     geom_density(data = external_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
 #   else if (sample_tcga %in% tcga_tmb_data_type$CANCER.TYPE)
 #     geom_density(data = tcga_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
 # } + scale_fill_discrete(name = "TMB Cohort") +
  
  theme_classic() + 
  theme(text = element_text(size = 25),
        legend.position = c(0.9, 0.9),
        plot.margin = unit(c(1, 1, 1, 1), "lines"),
        panel.grid = element_blank(), 
        line = element_blank(),
        legend.background = element_rect(fill='transparent')
  )

dev.off()
