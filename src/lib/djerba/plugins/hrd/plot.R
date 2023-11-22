#! /usr/bin/env Rscript

library(dplyr)
library(ggplot2)
library(optparse)
library(scales)
library(cowplot)

option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="Input report directory path", metavar="character")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
work_dir <- opt$dir

hrd_color <- c("#242424" ,"#d2d2d2","#999999",  "#e8e8e8" ,"#000000")
options(bitmapType='cairo')

cutoff_low = 0.7
cutoff_high = cutoff_low

boot <- read.table(paste(work_dir, 'hrd.tmp.txt', sep='/'),header=FALSE)

names(boot) <- c("var","q1","median_value","q3")
boot$Sample <- "Sample"

hrd_median <- as.numeric(unique(boot$median_value[boot$var == "Probability.w"])) 
intercept  <- boot$median_value[boot$var == "intercept.w"]

weights_df <- boot[boot$var %in% c("del.mh.prop.w","SNV3.w","SV3.w","SV5.w","hrd.w"),]

#equation [4] in Davies et al. 2017
weights_df$probability <- 1 / ( 1 + exp(-(intercept + weights_df$median_value)))

weights_df$var_long[weights_df$var == "SV5.w"] <- "Large Deletions"
weights_df$var_long[weights_df$var == "SV3.w"] <- "Tandem Duplications"
weights_df$var_long[weights_df$var == "SNV3.w"] <- "COSMIC SBS3"
weights_df$var_long[weights_df$var == "hrd.w"] <- "LOH"
weights_df$var_long[weights_df$var == "del.mh.prop.w"] <- "Microhomologous Deletions"
weights_df$var_longer <- paste0(weights_df$var_long,": ", round(weights_df$probability,2))

weights_df <- weights_df[order(weights_df$var_long,decreasing = T),]

weights_df$probability_cum <- cumsum(weights_df$probability)
weights_df$probability_cum_half <- (weights_df$probability / 2) + c(0,weights_df$probability_cum[-5])


out_path <- paste(work_dir, 'hrd.svg', sep='/')

svg(out_path, width = 8, height = 1.5, bg = "transparent")


  print(
    ggplot(weights_df ,aes(x="Sample",y=as.numeric(probability))) + 
      
      geom_bar(aes(fill=var_longer),stat ="identity",width=0.5, color = "white") + 
      
      annotate(x = 0, xend=2, y=cutoff_low, yend=cutoff_low, geom="segment",colour = "gray",linetype="dashed") +
      annotate(geom="text",x = 0,y=cutoff_low/2,color="gray30",label="HR-P", hjust = 0.5, vjust = 2,size=4) +
      
      annotate(geom="text",x = 0,y=(cutoff_high + max(hrd_median, 0.40))/2, color="gray30",label="HR-D", hjust = 0.5, vjust = 2,size=4) +
      
   #   geom_point(aes(y=as.numeric(probability_cum_half),x=c(1,1,1,1,1))) +
      
   #  geom_segment(aes(yend= c(0.1,0.37,0.55,0.68,0.85), xend=c(1.7,1.7,1.7,1.7,1.7),y=as.numeric(probability_cum_half),x=c(1,1,1,1,1))) +
   #   geom_label(aes(label=var_longer,y=c(0,0.31,0.54,0.73,0.95), x=c(0,0, 0, 0,0)), vjust = 0, fill="white", label.padding = unit(3, "point"))+
      
      scale_y_continuous( limit = c(0,1)) + 
      scale_fill_manual(values=hrd_color) +
      scale_color_manual(values=hrd_color) +
      
     # guides(fill='none')+
      theme_bw(base_size = 15) + 
      theme(
        axis.title=element_blank(),
        axis.text.y=element_blank(),
        axis.ticks.y=element_blank(),
        text = element_text(size = 15),
        panel.grid = element_blank(), 
        plot.margin = unit(c(t=10, r=0, b=0, l=0), "points"),
        line = element_blank(),
        panel.background = element_rect(fill = "transparent", colour = NA),
        plot.background = element_rect(fill="transparent",color=NA),
        plot.title = element_text(hjust = 0.5),
        legend.title=element_blank(),
        legend.justification="right",
        legend.margin=margin(0,0,0,0),
        legend.box.margin=margin(l=-10,r=5,t=-10,b=0)
      ) +
     labs(fill="")+
      
      coord_flip() 
  )

dev.off()

  
txt <- paste(readLines(paste(work_dir,"hrd.svg",sep="/")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)
