#! /usr/bin/env Rscript

library(dplyr)
library(ggplot2)
library(optparse)
library(scales)


option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="Input report directory path", metavar="character"),
  make_option(c("-m", "--marker"), type="character", default=NULL, help="msi", metavar="character"),
  make_option(c("-c", "--code"), type="character", default=NULL, help="TCGA code", metavar="character"),
  make_option(c("-t", "--tmb"), type="numeric", default=NULL, help="TMB per Mb", metavar="numeric")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
biomarker <- opt$marker
sampleTMB <- opt$tmb
sample_tcga <- opt$code
work_dir <- opt$dir


if(biomarker=="tmb"){
  
  data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')
  
  external_tmb_file <- paste(data_dir, 'tmbcomp-externaldata.txt', sep='/')
  external_tmb_data <- read.delim(external_tmb_file, header = TRUE, stringsAsFactors = F)
  tcga_tmb_file <- paste(data_dir, 'tmbcomp-tcga.txt', sep='/')
  tcga_tmb_data <- read.delim(tcga_tmb_file, header = TRUE, stringsAsFactors = F)
  
  #subset external data to cancer type
  external_tmb_data_type <- external_tmb_data %>% filter(if (sample_tcga %in% external_tmb_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)
  #subset tcga data to cancer type
  tcga_tmb_data_type <- tcga_tmb_data %>% filter(if (sample_tcga %in% tcga_tmb_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)
  
  
  if (sample_tcga %in% external_tmb_data_type$CANCER.TYPE){
    median_tmb <- median(external_tmb_data_type$tmb)
    cohort_label <- paste(toupper(sample_tcga) ,"Cohort")
  }
  else if (sample_tcga %in% tcga_tmb_data_type$CANCER.TYPE){
    median_tmb <- median(tcga_tmb_data_type$tmb)
    cohort_label <- paste("TCGA",toupper(sample_tcga),"Cohort")
  }
  else{
    median_tmb <- median(tcga_tmb_data$tmb)
    cohort_label <- "All TCGA "
}
  
  tmb_path <- paste(work_dir, 'tmb.svg', sep='/')
  
  svg(tmb_path, width = 8, height = 1.6, bg = "transparent")
  print(
  ggplot(tcga_tmb_data) + 
    {
      if (sample_tcga %in% external_tmb_data_type$CANCER.TYPE)
        geom_boxplot(data = external_tmb_data_type, aes(x=0,y=tmb,color="Cohort"),width = 0.1, outlier.shape = NA) 
        
      else if (sample_tcga %in% tcga_tmb_data_type$CANCER.TYPE)
        geom_boxplot(data = tcga_tmb_data_type, aes(x=0,y=tmb,color="Cohort"), width = 0.1, outlier.shape = NA) 
      else
        geom_boxplot(aes(x=0,y=tmb,color="All TCGA"),width = 0.1, outlier.shape = NA) 
    } +

    annotate( geom="segment", x = -0.1, xend=0.1, y=10, yend=10, colour = "gray") +
    
    annotate(geom="text",y = 5,x=0,color="gray30",label="TMB-L",  vjust = -4.5, size=4) +
    annotate(geom="text",y = (10 + max(sampleTMB, 15))/2,x=0,color="gray30",label="TMB-H",  vjust = -4.5, size=4) +
    annotate(geom="text",y = median_tmb, x=0,color="black",label=cohort_label, vjust = -2, hjust=0.25, size=4) +
    annotate(geom="text",y = sampleTMB,x=0,color="red",label="This Sample",  vjust = 2.7, hjust=0.7,  size=4) +
    
    annotate(geom="point",y = sampleTMB,x=0,color="red",shape=1, size=8) +
    annotate(geom="point",y = sampleTMB,x=0,color="red",shape=20, size=3) +
    
    labs(x="",y="coding mutations per Mb",color="",title="",shape="",size="") +
    scale_color_manual( values= c( "gray30", "red") ) +
    scale_shape_manual(values=c(16,1)) +
    theme_classic() +
    guides(shape="none",size="none",color="none") + 
    scale_y_continuous( limits = c(0, max(sampleTMB, 15))) +
    coord_flip(clip = "off") +
    theme(
      axis.line.y = element_blank(),
      panel.grid = element_blank(), 
      text = element_text(size = 16, family = "TT Arial"),
      legend.title=element_blank(),
      plot.margin = unit(c(t=0, r=6, b=0, l=-20), "points"),
      axis.title.y=element_blank(),
      axis.text.y=element_blank(),
      axis.ticks.y=element_blank(),
      line = element_blank(),
      panel.background = element_rect(fill = "transparent", colour = NA),
      plot.background = element_rect(fill="transparent",color=NA)
      
    )
  )
  dev.off()

}
