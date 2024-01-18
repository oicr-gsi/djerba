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
weights_df$var_longer <- paste0(weights_df$var_long,": ", sprintf("%0.2f", round(weights_df$probability, digits = 2)))

weights_df <- weights_df[order(weights_df$var_long,decreasing = T),]

weights_df$probability_cum <- cumsum(weights_df$probability)
weights_df$probability_cum_half <- (weights_df$probability / 2) + c(0,weights_df$probability_cum[-5])


out_path <- paste(work_dir, 'hrd.stacked.svg', sep='/')

svg(out_path, width = 8, height = 1.5, bg = "transparent")


  print(
    ggplot(weights_df ,aes(x="Sample",y=as.numeric(probability))) + 
      
      geom_bar(aes(fill=var_longer),stat ="identity",width=0.5, color = "white") + 
      
      annotate(x = 0, xend=2, y=cutoff_low, yend=cutoff_low, geom="segment",colour = "gray",linetype="dashed") +
      annotate(geom="text",x = 0,y=cutoff_low/2,color="gray30",label="HR-P", hjust = 0.5, vjust = 2,size=4) +
      annotate(geom="text",x = 0,y=(cutoff_high + max(hrd_median, 0.40))/2, color="gray30",label="HR-D", hjust = 0.5, vjust = 2,size=4) +
      
      scale_y_continuous( limit = c(0,1)) + 
      scale_fill_manual(values=hrd_color) +
      scale_color_manual(values=hrd_color) +
      
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

adjust_label_w_position =0.25
if(boot$median_value[boot$var == "Probability.w"] > 0.5){
  adjust_label_w_position =0.8
}

out_path <- paste(work_dir, 'hrd.svg', sep='/')

svg(out_path, width = 8, height = 1.5, bg = "transparent")

print(
  
  ggplot(weights_df,aes(x="Sample",y=as.numeric(probability))) + 
    geom_bar(aes(fill=var_longer),stat ="identity",width=0.5, color = "white") + 
    scale_fill_manual(values=c("white","white","white","white","white")) +

    geom_errorbar(aes(ymin=as.numeric(boot$q1[boot$var == "Probability.w"]), ymax=as.numeric(boot$q3[boot$var == "Probability.w"])), width=0, linewidth=1, color="red") +
    
    annotate(x = 0, xend=2, y=cutoff_low, yend=cutoff_low,geom="segment",colour = "gray") +
    annotate(geom="text",x = 0,y=cutoff_low/2,color="gray30",label="HR-P", hjust = 0.5, vjust = -5,size=4) +
    
    annotate(x = 0, xend=2, y=cutoff_low, yend=cutoff_low,geom="segment", colour = "gray") +
    annotate(geom="text",x = 0,y=0.85, color="gray30",label="HR-D", hjust = 0.5, vjust = -5,size=4) +
    
    annotate(geom="point",y = boot$median_value[boot$var == "Probability.w"], x="Sample", color="red",shape=1, size=8) +
    annotate(geom="point",y = boot$median_value[boot$var == "Probability.w"], x="Sample", color="red",shape=20, size=3) +
   annotate(geom="text",y = boot$median_value[boot$var == "Probability.w"], x=0, color="red",label="This Sample",  vjust = -0.75, hjust=adjust_label_w_position,  size=4) +
   
    theme_classic() + 
    labs(x="",y="HRD probability",title="") + 
    scale_y_continuous( limit = c(0, max(boot$median_value[boot$var == "Probability.w"], 1))) + 

    coord_flip() +
    
    scale_color_manual(values=c("#65bc45","#000000","#0099ad")) +
    theme(
      axis.line.y = element_blank(),
      legend.title=element_blank(),
      axis.title.y=element_blank(),
      legend.text.align = 1,
      axis.text.y=element_blank(),
      axis.ticks.y=element_blank(),
      text = element_text(size = 16, family = "TT Arial"),
      panel.grid = element_blank(), 
      plot.margin = unit(c(t=-20, r=-10, b=0, l=0), "points"),
      line = element_blank(),
      panel.background = element_rect(fill = "transparent", colour = NA),
      plot.background = element_rect(fill="transparent",color=NA),
      legend.box.margin=margin(l=-10,r=5,t=20,b=0)
      
    ) 
  
)
dev.off()

txt <- paste(readLines(paste(work_dir,"hrd.svg",sep="/")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)
