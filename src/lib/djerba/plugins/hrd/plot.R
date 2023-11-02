#! /usr/bin/env Rscript

library(dplyr)
library(ggplot2)
library(optparse)
library(scales)


option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="Input report directory path", metavar="character")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
work_dir <- opt$dir

cutoff_low = 0.7
cutoff_high = cutoff_low

hrd_path <- paste(work_dir, 'hrd.tmp.txt', sep='/')

boot <- read.table(hrd_path,header=FALSE)

names(boot) <- c("q1","median_value","q3")
boot$Sample <- "Sample"
hrd_median <- as.numeric(unique(boot$median_value)) 

out_path <- paste(work_dir, 'hrd.svg', sep='/')

options(bitmapType='cairo')
svg(out_path, width = 8, height = 1.6, bg = "transparent")
print(
  
  ggplot(boot,aes(x="Sample")) + 
    geom_errorbar(aes(ymin=as.numeric(q1), ymax=as.numeric(q3)), width=0, linewidth=1, color="red") +
    
    annotate(x = 0, xend=2, y=cutoff_low, yend=cutoff_low,geom="segment",colour = "gray") +
    annotate(geom="text",x = 0,y=cutoff_low/2,color="gray30",label="HR-P", hjust = 0.5, vjust = -6,size=4) +
    
    annotate(x = 0, xend=2, y=cutoff_high, yend=cutoff_high,geom="segment", colour = "gray") +
    annotate(geom="text",x = 0,y=(cutoff_high + max(hrd_median, 0.40))/2, color="gray30",label="HR-D", hjust = 0.5, vjust = -6,size=4) +
    
    annotate(geom="point",y = hrd_median, x="Sample",color="red",shape=1, size=8) +
    annotate(geom="point",y = hrd_median, x="Sample",color="red",shape=20, size=3) +
    
    theme_classic() + 
    labs(x="",y="HRD Score",title="") + 
    scale_y_continuous( limit = c(0, max(hrd_median, 0.40))) + 
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
      plot.margin = unit(c(t=-20, r=-10, b=0, l=0), "points"),
      line = element_blank(),
      panel.background = element_rect(fill = "transparent", colour = NA),
      plot.background = element_rect(fill="transparent",color=NA)
      
    ) 
  
)
dev.off()
  
txt <- paste(readLines(paste(work_dir,"hrd.svg",sep="/")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)
