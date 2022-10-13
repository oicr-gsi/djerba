#! /usr/bin/env Rscript

library(dplyr)
library(ggplot2)
library(optparse)

option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="Input report directory path", metavar="character"),
  #make_option(c("-o", "--output"), type="character", default=NULL, help="svg output path", metavar="character"),
  make_option(c("-m", "--msi"), type="character", default="TRUE", help="msi", metavar="character")

)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
msi_b <- opt$msi

work_dir <- opt$dir

if(msi_b == "TRUE"){
  msi_path <- paste(work_dir, 'msi.txt', sep='/')
  
  boot <- read.table(msi_path)
  
  names(boot) <- c("q0","q1","median","q3","q4")
  boot$Sample <- "Sample"
  
  msi_out_path <- paste(work_dir, 'msi.svg', sep='/')
  
  options(bitmapType='cairo')
  svg(msi_out_path, width = 8, height = 1.5)
  print(
    
  ggplot(boot,aes(x="Sample")) + 
    geom_bar(aes(y=log(median)),fill='grey',stat ="identity",alpha=0.5,color="black") + 
    geom_errorbar(aes(ymin=log(q1), ymax=log(q3)), width=0,size=2) +
    geom_errorbar(aes(ymin=log(q0), ymax=log(q4)), width=0) +
    
    annotate(x = 0, xend=2, y=log(5), yend=log(5),geom="segment",linetype="longdash",colour = "red") +
    annotate(geom="text",x = 0,y=log(5),color="black",label="MSI-H", hjust = -0.25, vjust = -6,size=3) +
    
    guides(fill=FALSE)+
    theme_classic() + 
    labs(x="",y="unstable microsatellites (%, log)",title="") + 
    scale_y_continuous(expand = c(0,0), limit = c(0, log(100))) + 
    guides(alpha="none")+
    coord_flip() +

    scale_color_manual(values=c("#65bc45","#000000","#0099ad")) +
    theme(#axis.text.y = element_text(angle = 90, vjust = 0.5, hjust=.5),
          axis.title.y=element_blank(),
          axis.text.y=element_blank(),
          axis.ticks.y=element_blank(),
          text = element_text(size = 10),
          panel.grid = element_blank(), 
          plot.margin = unit(c(10, 10, 10, 10), "points"),
          line = element_blank()
          ) 
  )
  dev.off()
  
}

