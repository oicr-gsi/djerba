#! /usr/bin/env Rscript

library(data.table)
library(cowplot)
library(optparse)
library(ggplot2)
library(dplyr)

captiv8_colors <- c("#91bfdb", "#d73027", "#4575b4",  "#fc8d59","#e0f3f8", "#fee090")

##in take##
option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="Input report directory path", metavar="character"),
  make_option(c("-i", "--input"), type="character", default=NULL, help="captiv8 result file", metavar="character")
)
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
work_dir <- opt$dir

input_path <- opt$input

captiv8 <- fread(input_path)

##Preprocess data for prettiness##
captiv8[captiv8 == "SWISNF"] <- "SWI/SNF"
captiv8$evidence[captiv8$evidence == "no" & (captiv8$marker == "Viral" | captiv8$marker == "SWI/SNF" )] <- "none\ndetected"
captiv8$evidence[captiv8$evidence == "cms_evidence" & (captiv8$marker == "CMS"  )] <- "not\napplicable"

##### PLOTTING ####
bar_charts <- 
plot_grid(
  ggplot(captiv8 %>% filter(marker == "CD8+"),aes(y=as.numeric(evidence),x=marker)) + 

  geom_bar(stat="identity",fill=captiv8_colors[1]) + 
  geom_text(aes(label=round(as.numeric(evidence),2)),  vjust=-0.25) +
  labs(title="CD8+ T cell\npopulation fraction") +
  scale_y_continuous(breaks=c(0,.09,.24,.59),limits = c(0,1)) +
  
  theme_bw(base_size = 15) + 
  theme(
    legend.background = element_rect(colour = NA,fill=NA),
    plot.margin = unit(c(0,0,0,0), "lines"),
    panel.grid.major.x = element_blank(), 
    panel.grid.minor = element_blank(),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    axis.title = element_blank(),
    plot.title = element_text(hjust = 0.5),
    
    panel.background = element_rect(fill = "transparent",colour = NA),
    plot.background = element_rect(fill = "transparent",colour = NA)
  ) 
    
,
ggplot(captiv8 %>% filter(marker == "TMB"),aes(y=as.numeric(evidence),x=marker)) + 
  geom_bar(stat="identity",fill=captiv8_colors[5]) + 
  geom_text(aes(label=round(as.numeric(evidence),2)),  vjust=-0.25) +
  labs(title="Genomic TMB\n(mut/MB)") +
  scale_y_continuous(breaks=c(0,8,10,20),limits = c(0,50)) +
  theme_bw(base_size = 15) +
  theme(
    legend.background = element_rect(colour = NA,fill=NA),
    plot.margin = unit(c(0,0,0,0), "lines"),
    panel.grid.major.x = element_blank(), 
    panel.grid.minor = element_blank(),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    axis.title = element_blank(),
    plot.title = element_text(hjust = 0.5),
    
    panel.background = element_rect(fill = "transparent",colour = NA),
    plot.background = element_rect(fill = "transparent",colour = NA)
  ) 

,
ggplot(captiv8 %>% filter(marker == "M1M2"),aes(y=as.numeric(evidence),x=marker)) + 
  geom_bar(stat="identity",fill=captiv8_colors[3]) +  
  geom_text(aes(label=round(as.numeric(evidence),2)),  vjust=-0.25) +
  labs(title="M1M2\nmacrophages (TPM)") +
  scale_y_continuous(breaks=c(0,6.96,22.84,41.29),limits = c(0,50)) +

  theme_bw(base_size = 15) +
  theme(
    legend.background = element_rect(colour = NA,fill=NA),
    plot.margin = unit(c(0,0,0,0), "lines"),
    panel.grid.major.x = element_blank(), 
    panel.grid.minor = element_blank(),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    axis.title = element_blank(),
    plot.title = element_text(hjust = 0.5),
    
    panel.background = element_rect(fill = "transparent",colour = NA),
    plot.background = element_rect(fill = "transparent",colour = NA)
  ) 

,

  ggplot(captiv8 ,aes(y=as.numeric(evidence),x=marker)) + 
  labs(y="Component-Result-CAPTIV-8 Scaled Score")+
  theme_bw(base_size = 15)+ xlim(0,0) + ylim(0,0)+
  annotate(geom="text",y = 0,x=0,label="}", size=30) +
   theme(axis.line=element_blank(),
         axis.text.x=element_blank(),
          axis.text.y=element_blank(),
         axis.ticks=element_blank(),
          axis.title.x=element_blank(),
         legend.position="none",
          panel.background=element_blank(),panel.border=element_blank(),panel.grid.major=element_blank(),
          panel.grid.minor=element_blank(),plot.background=element_blank())
, ncol = 4, align = 'hv',axis = 'tbrl',rel_widths = c(3,3,3,2))

text_charts <- 
plot_grid(
ggplot(captiv8 %>% filter(marker == " Viral"),aes(y=as.numeric(evidence),x=marker)) + 
  annotate("rect", xmin = -1, xmax = 1, ymin = -1, ymax = 1,fill="white") +
  
   annotate(geom="text",y = 0,x=0,color="black",label=captiv8$evidence[captiv8$marker == "Viral"], size=7) +
  theme_bw(base_size = 15)  +
  theme(
    legend.background = element_rect(colour = NA,fill=NA),
    plot.margin = unit(c(0,0,0,0), "lines"),
    panel.grid.major = element_blank(), 
    panel.grid.minor = element_blank(),
    axis.title=element_blank(),
    axis.text=element_blank(),
    axis.ticks=element_blank(),
    plot.title = element_text(hjust = 0.5),
    panel.background = element_rect(fill = captiv8_colors[6],colour = NA),
    legend.justification = c(0,0.5)
  ) + labs(title="Cancer-related\nviral integration")
,
ggplot(captiv8 %>% filter(marker == "SWI/SNF"),aes(y=as.numeric(evidence),x=marker)) + 
  annotate("rect", xmin = -1, xmax = 1, ymin = -1, ymax = 1,fill="white") +
  
   annotate(geom="text",y = 0,x=0,color="black",label=captiv8$evidence[captiv8$marker == "SWI/SNF"], size=7) +
  
  ylim(-1,1)+
  theme_bw(base_size = 15)  +
  theme(
    legend.background = element_rect(colour = NA,fill=NA),
    plot.margin = unit(c(0,0,0,0), "lines"),
    panel.grid.major = element_blank(), 
    panel.grid.minor = element_blank(),
    axis.title=element_blank(),
    axis.text=element_blank(),
    axis.ticks=element_blank(),
    plot.title = element_text(hjust = 0.5),
    panel.background = element_rect(fill = captiv8_colors[4],colour = NA),
    legend.justification = c(0,0.5)
  )+ labs(title="loss-of-function\nSWI/SNF pathway\nmutation")
,
ggplot(captiv8 %>% filter(marker == "CMS"),aes(y=as.numeric(evidence),x=marker)) + 
  annotate("rect", xmin = -1, xmax = 1, ymin = -1, ymax = 1,fill="white") +
  annotate(geom="text",y = 0,x=0,color="black",label=captiv8$evidence[captiv8$marker == "CMS"], size=7) +
  theme_bw(base_size = 15)  +
  theme(
    legend.background = element_rect(colour = NA,fill=NA),
    plot.margin = unit(c(0,0,0,0), "lines"),
    panel.grid.major = element_blank(), 
    panel.grid.minor = element_blank(),
    axis.title=element_blank(),
    axis.text=element_blank(),
    axis.ticks=element_blank(),
    plot.title = element_text(hjust = 0.5),
    panel.background = element_rect(fill = captiv8_colors[2],colour = captiv8_colors[2]),
    legend.justification = c(0,0.5))+ 
  labs(title="Molecular\nsubgroup of\ncolorectal cancer")
  
, ncol = 1, align = 'hv',axis = 'tbrl')

captiv8_card <- 
plot_grid(text_charts,bar_charts, ncol = 2, align = 'hv',axis = 'tbrl',rel_widths = c(.2,.8))



captiv8_el <- 
ggplot(captiv8 %>% filter(marker %in% c("CD8+" , "M1M2"    ,"SWI/SNF" , "TMB"   ,   "Viral",
                                         "CMS")),aes(x="CAPTIV-8score",y=as.numeric(score))) + 
  geom_bar(aes(fill=marker),stat ="identity") + 

  annotate(x = 0, xend=2, y=5, yend=5,geom="segment",linetype="longdash",colour = "red") +

  theme_bw(base_size = 15) + 
  labs(x="",title="Collated\nScore") + 
  scale_y_continuous(breaks=c(5,24), limit = c(0, 24)) + 
 guides(alpha="none",color="none",fill="none")+

  scale_fill_manual(values=captiv8_colors) +
  theme(
    axis.title=element_blank(),
    axis.text.x=element_blank(),
    axis.ticks.x=element_blank(),
    text = element_text(size = 15),
    panel.grid = element_blank(), 
    plot.margin = unit(c(t=10, r=0, b=0, l=0), "points"),
    line = element_blank(),
    plot.title = element_text(hjust = 0.5)
  ) 

out_path <- paste(work_dir, 'captiv8.svg', sep='/')

options(bitmapType='cairo')
svg(out_path, width = 11, height = 6, bg = "transparent")

  print(
  plot_grid(captiv8_card,captiv8_el, align = 'hv',axis = 'tbrl', ncol = 2,rel_widths = c(3,.5))
  )
dev.off()

txt <- paste(readLines(paste(work_dir,"captiv8.svg",sep="/")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)
