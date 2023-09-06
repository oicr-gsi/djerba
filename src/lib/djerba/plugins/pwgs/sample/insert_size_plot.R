#! /usr/bin/env Rscript

library(ggplot2)
library(cowplot)
library(optparse)
library(data.table)
library(dplyr)
options(scipen=0.1)

option_list = list(
  make_option(c("-i", "--insert_size_file"), type="character", default=NULL, help="input file", metavar="character"),
  make_option(c("-o", "--output_directory"), type="character", default=NULL, help="output directory", metavar="character")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE);
opt <- parse_args(opt_parser)

# set better variable names
insert_size_file <- opt$insert_size_file
output_directory <- opt$output_directory

insert_size <- fread(insert_size_file)

insert_size <- insert_size %>% 
  summarise(insert_size=size,count=count,read_freq=(count/sum(count))*100)

options(bitmapType='cairo')
svg(paste(output_directory,"insert_size_distribution.svg",sep="/"), width = 7, height = 4)

plot_grid(
ggplot(insert_size,aes(x=insert_size)) + 

    geom_line(aes(y=read_freq)) +
    
    theme_bw(base_size=18) + 
    labs(x="Insert Size (bp)",y="Fraction of Inserts (%)",color="Donor") +
    theme(
      legend.background = element_rect(colour = NA,fill=NA),
      plot.margin = unit(c(0,0,0,0), "lines"),
      panel.grid.minor = element_blank(),
      panel.background = element_rect(fill = "transparent",colour = NA),
      plot.background = element_rect(fill = "transparent",colour = NA),
      legend.justification = c(0,0.5),
      axis.title.x=element_blank(),
      axis.text.x=element_blank(),
      axis.ticks.x=element_blank()
      
    ) + scale_x_continuous(breaks=c(0,50,167,250,334,501),limits = c(0,501)) 
  
,
ggplot(insert_size,aes(x="",y=insert_size,fill=read_freq)) + 
  geom_tile() +   
  theme_bw(base_size=22) + 
  scale_fill_gradient(low="white", high="black") + 
  labs(y="Insert Size (bp)",fill="Insert Fraction (%)") + 
  guides(fill="none") +
  theme(
    legend.background = element_rect(colour = NA,fill=NA),
    plot.margin = unit(c(0,0,0,0), "lines"),
    panel.grid = element_blank(),
    panel.background = element_rect(fill = "transparent",colour = NA),
    plot.background = element_rect(fill = "transparent",colour = NA),
    axis.title.y=element_blank(),
    axis.text.y=element_blank(),
    axis.ticks.y=element_blank()
  ) +  scale_y_continuous(breaks=c(0,167,250,334,501),limits = c(0,501)) +
  coord_flip(clip = "off") 
, ncol = 1, align = 'v',axis = 'tbrl',labels = c("",""),rel_heights = c(0.7,0.3))

dev.off()
