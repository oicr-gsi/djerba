#! /usr/bin/env Rscript

library(dplyr)
library(ggplot2)
library(optparse)
library(scales)


option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="Input report directory path", metavar="character"),
  make_option(c("-m", "--marker"), type="character", default="msi", help="msi", metavar="character")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
biomarker <- opt$marker
work_dir <- opt$dir

cutoff_MSS = 5
cutoff_MSI = 15

if(biomarker=="msi"){
  
  msi_path <- paste(work_dir, 'msi.txt', sep='/')
  
  boot <- read.table(msi_path,header=FALSE)
  
  names(boot) <- c("q0","q1","median_value","q3","q4")
  boot$Sample <- "Sample"
  
  msi_out_path <- paste(work_dir, 'msi.svg', sep='/')
  
  msi_median <- as.numeric(unique(boot$median_value))
  
  options(bitmapType='cairo')
  svg(msi_out_path, width = 8, height = 1.6, bg = "transparent")
  print(
    
  ggplot(boot,aes(x="Sample")) + 
    geom_errorbar(aes(ymin=as.numeric(q1), ymax=as.numeric(q3)), width=0, linewidth=1, color="red") +
    
    annotate(x = 0, xend=2, y=cutoff_MSS, yend=cutoff_MSS,geom="segment",colour = "gray") +
    annotate(geom="text",x = 0,y=cutoff_MSS/2,color="gray30",label="MSS", hjust = 0.5, vjust = -6,size=4) +
    
    annotate(x = 0, xend=2, y=cutoff_MSI, yend=cutoff_MSI,geom="segment", colour = "gray") +
    annotate(geom="text",x = 0,y=(cutoff_MSI + max(msi_median, 40))/2, color="gray30",label="MSI", hjust = 0.5, vjust = -6,size=4) +
    
    annotate(x = 0, xend=2, y=cutoff_MSI, yend=cutoff_MSI,geom="segment", colour = "gray") +
    annotate(geom="text",x = 0,y=(cutoff_MSI + cutoff_MSS)/2, color="gray30",label="Inconclusive", hjust = 0.5, vjust = -6,size=4) +
    
    
    annotate(geom="point",y = msi_median, x="Sample",color="red",shape=1, size=8) +
    annotate(geom="point",y = msi_median, x="Sample",color="red",shape=20, size=3) +
    annotate(geom="text",y = msi_median,x=0,color="red",label="This Sample",  vjust = -0.9, hjust=0.25,  size=4) +
    
    theme_classic() + 
    labs(x="",y="unstable microsatellites (%)",title="") + 
    scale_y_continuous( limit = c(0, max(msi_median, 40))) + 
    guides(fill="none", alpha="none")+
    coord_flip() +

    scale_color_manual(values=c("#65bc45","#000000","#0099ad")) +
    theme(
          axis.line.y = element_blank(),
          legend.title=element_blank(),
          axis.title.y=element_blank(),
          axis.text.y=element_blank(),
          axis.ticks.y=element_blank(),
          text = element_text(size = 18),
          panel.grid = element_blank(), 
          plot.margin = unit(c(t=-20, r=-20, b=0, l=-20), "points"),
          line = element_blank(),
          panel.background = element_rect(fill = "transparent", colour = NA),
          plot.background = element_rect(fill="transparent",color=NA)

    ) 

  )
  dev.off()
  
}
