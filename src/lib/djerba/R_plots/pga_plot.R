#! /usr/bin/env Rscript

library(dplyr)
library(ggplot2)
library(optparse)
library(scales)

option_list = list(
    make_option(c("-o", "--output"), type="character", default=NULL, help="SVG output path", metavar="character"),
    make_option(c("-p", "--pga"), type="numeric", default=NULL, help="Percent Genome Altered", metavar="numeric")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

samplePGA <- as.numeric(opt$pga)
out_path <- opt$output

data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')
tcga_pga_file <- paste(data_dir, 'pgacomp-tcga.txt', sep='/')
tcga_pga_data <- read.table(tcga_pga_file, header = TRUE, stringsAsFactors = F,sep = "\t")

options(bitmapType='cairo')

vline_top <- max(density(tcga_pga_data$PGA)$y)
label_location <- vline_top * 1.25
label_x_offset <- 5

svg(out_path, width=8, height=3)
ggplot(tcga_pga_data, aes(x=PGA)) +
  geom_density(aes(fill = "All TCGA"), alpha = 0.5) + 
  scale_x_continuous(expand = c(0, 0), limit = c(0, max(samplePGA,  100))) +
  scale_y_continuous(expand = c(0, 0),labels = percent) +

  geom_segment(x=samplePGA, y=0, xend=samplePGA, yend=vline_top, linetype="solid",colour = "black")+
  annotate(y=label_location,geom="text",x = samplePGA-label_x_offset,color="black",label="This tumour", hjust =-0.02,size=5,vjust=2) +

  labs(x="Percent Genome Altered",fill="Cohort",y="% of samples") +

  theme_classic() + 
  theme(text = element_text(size = 25),
        plot.margin = unit(c(1, 1, 1, 1), "lines"),
        panel.grid = element_blank(), 
        line = element_blank(),
        legend.background = element_rect(fill='transparent')
  )

dev.off()
