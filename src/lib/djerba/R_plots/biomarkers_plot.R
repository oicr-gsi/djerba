#! /usr/bin/env Rscript

library(dplyr)
library(ggplot2)
library(optparse)

option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="Input report directory path", metavar="character"),
  make_option(c("-o", "--output"), type="character", default=NULL, help="svg output path", metavar="character")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
msi_path <- paste(opt$dir, 'msi.txt', sep='/')
out_path <- opt$output

##test##
#setwd('/Volumes/')
#file <- 'cgi/scratch/fbeaudry/msi_test/BTC_0013/BTC_0013_Lv_P_WG_HPB-199_LCM.filter.deduped.realigned.recalibrated.msi.booted'

boot <- read.table(msi_path)

names(boot) <- c("q0","q1","median","q3","q4")
boot$Sample <- "Sample"


options(bitmapType='cairo')
svg(out_path, width = 5, height = 1.5)

ggplot(boot,aes(x="Sample")) + 
  geom_bar(aes(y=median,fill=ifelse(median < 5,'red','green')),stat ="identity") + 
  geom_errorbar(aes(ymin=q1, ymax=q3), width=0,size=2) +
  geom_errorbar(aes(ymin=q0, ymax=q4), width=0) +
  
  geom_hline(yintercept = 5,color=ifelse(boot$median < 5,'black','white'))+
  guides(fill=FALSE)+
  theme_bw(base_size=15) + 
  labs(x="",title="MSS                                                                               MSI",y="unstable microsatellites (%)") + 
  ylim(0,100) + guides(alpha="none")+
  
  scale_color_manual(values=c("#65bc45","#000000","#0099ad")) +
  theme(axis.text.y = element_text(angle = 90, vjust = 0.5, hjust=.5)) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank()) +
  theme(axis.title.y=element_blank(),
    axis.text.y=element_blank(),
    axis.ticks.y=element_blank())  + coord_flip()

dev.off()

