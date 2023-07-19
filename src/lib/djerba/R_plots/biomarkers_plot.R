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

cutoff_MSS = 5
cutoff_MSI = 15

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
  
  median_tmb <- median(tcga_tmb_data$tmb)
  tmb_path <- paste(work_dir, 'tmb.svg', sep='/')
  
  svg(tmb_path, width = 8, height = 1.6, bg = "transparent")
  print(
  ggplot(tcga_tmb_data) + 
    {
      if (sample_tcga %in% external_tmb_data_type$CANCER.TYPE)
        geom_boxplot(data = external_tmb_data_type, aes(x=0,y=tmb,color="Cohort"),width = 0.05, outlier.shape = NA) 
        
      else if (sample_tcga %in% tcga_tmb_data_type$CANCER.TYPE)
        geom_boxplot(data = tcga_tmb_data_type, aes(x=0,y=tmb,color="Cohort"),width = 0.05, outlier.shape = NA) 
      else
        geom_boxplot(aes(x=0,y=tmb,color="All TCGA"),width = 0.05, outlier.shape = NA) 
    } +
  #  geom_hline(yintercept = 1,alpha=0.25,color="white")  +
  #  geom_hline(yintercept = max(sampleTMB, 25), alpha=0.25,color="white")  +
    
    annotate( geom="segment", x = -0.1, xend=0.1, y=10, yend=10, colour = "gray") +
    
    annotate(geom="text",y = 10,x=0,color="gray30",label="TMB-H Cutoff",  vjust = -4.5, size=4) +
    annotate(geom="text",y = median_tmb, x=0,color="black",label="Cohort", hjust = 0.3, vjust = 3, size=4) +
    annotate(geom="text",y = sampleTMB,x=0,color="red",label="This Sample",  vjust = -2.5,size=4) +
    
    annotate(geom="point",y = sampleTMB,x=0,color="red",shape=1, size=5) +
    annotate(geom="point",y = sampleTMB,x=0,color="red",shape=20, size=1.5) +
    
    labs(x="",y="coding mutations/mb",color="",title="",shape="",size="") +
    scale_color_manual( values= c( "gray30", "red") ) +
    scale_shape_manual(values=c(16,1)) +
    theme_classic() +
    guides(shape="none",size="none",color="none") + 
    scale_y_continuous( limits = c(0, max(sampleTMB, 25))) +
    coord_flip(clip = "off") +
    theme(
      axis.line.y = element_blank(),
      panel.grid = element_blank(), 
      text = element_text(size = 18),
      legend.title=element_blank(),
      plot.margin = unit(c(0, 12, 0, 4), "points"),
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

if(biomarker=="msi"){
  
  msi_path <- paste(work_dir, 'msi.txt', sep='/')
  
  boot <- read.table(msi_path,header=FALSE)
  
  names(boot) <- c("q0","q1","median","q3","q4")
  boot$Sample <- "Sample"
  
  msi_out_path <- paste(work_dir, 'msi.svg', sep='/')
  
  options(bitmapType='cairo')
  svg(msi_out_path, width = 8, height = 1.6, bg = "transparent")
  print(
    
  ggplot(boot,aes(x="Sample")) + 
    geom_errorbar(aes(ymin=q1, ymax=q3), width=0, linewidth=2) +
    
    annotate(x = 0, xend=2, y=cutoff_MSS, yend=cutoff_MSS,geom="segment",colour = "gray") +
    annotate(geom="text",x = 0,y=0,color="gray30",label="MSS", hjust = 0, vjust = -4.1,size=4) +
    
    annotate(x = 0, xend=2, y=cutoff_MSI, yend=cutoff_MSI,geom="segment", colour = "gray") +
    annotate(geom="text",x = 0,y=cutoff_MSI,color="gray30",label="MSI", hjust = -0.2, vjust = -4.1,size=4) +
    
    geom_bar(aes(y=median),fill='gray',stat ="identity",alpha=0.5,colour="red") + 
    geom_errorbar(aes(ymin=q0, ymax=q4), width=0,colour="red") +
    
    
    theme_classic() + 
    labs(x="",y="unstable microsatellites (%)",title="") + 
    scale_y_continuous(expand = c(0,0), limit = c(0, 100)) + 
    guides(fill="none", alpha="none")+
    coord_flip() +

    scale_color_manual(values=c("#65bc45","#000000","#0099ad")) +
    theme(
          axis.title.y=element_blank(),
          axis.text.y=element_blank(),
          axis.ticks.y=element_blank(),
          text = element_text(size = 18),
          panel.grid = element_blank(), 
          plot.margin = unit(c(0, 12, 0, 4), "points"),
          line = element_blank(),
          panel.background = element_rect(fill = "transparent", colour = NA),
          plot.background = element_rect(fill="transparent",color=NA)

    ) 

  )
  dev.off()
  
}

