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

cutoff_low = 0.7
cutoff_high = cutoff_low

hrd_path <- paste(work_dir, 'hrd.tmp.txt', sep='/')

boot <- read.table(hrd_path,header=FALSE)

names(boot) <- c("var","q1","median_value","q3")
boot$Sample <- "Sample"
hrd_median <- as.numeric(unique(boot$median_value[boot$var == "Probability.w"])) 



stacks_df <- boot[boot$var %in% c("del.mh.prop","SNV3","SV3","SV5","hrd"),]

options(bitmapType='cairo')

gg_theme <- theme(
  legend.background = element_rect(colour = NA,fill=NA),
  plot.margin = unit(c(0,0,0,0), "lines"),
  panel.grid.major.x = element_blank(), 
  panel.grid.minor = element_blank(),
 # axis.text.x = element_blank(),
 # axis.ticks.x = element_blank(),
  axis.title.x = element_blank(),
 axis.title.y = element_text(angle = 0, vjust = 0.05),
  panel.background = element_rect(fill = "transparent",colour = NA),
  plot.background = element_rect(fill = "transparent",colour = NA)
)


bars <- 

    plot_grid(
      ggplot(stacks_df %>% filter(var == "del.mh.prop"),aes(y="",x=median_value)) + 
        
        geom_bar(stat="identity",fill="black") + 
        scale_x_continuous(limits = c(0,1)) +
        
        theme_bw(base_size = 15) + labs(y=expression(paste("Proportion of\ndeletions at micro-\nhomologous sites"))) +
       gg_theme
      
      ,
      ggplot(stacks_df %>% filter(var == "SNV3"),aes(y="",x=median_value)) + 
        
        geom_bar(stat="identity",fill="black") + 
        scale_x_continuous(limits = c(0, 600)) +
        
        theme_bw(base_size = 15) + labs(y=expression(paste("COSMIC SNV\nSignatures 3 and 8"))) +
        gg_theme
      
      ,       
      ggplot(stacks_df %>% filter(var == "SV3"),aes(y="",x=median_value)) + 
        
        geom_bar(stat="identity",fill="black") + 
        scale_x_continuous(limits = c(0,200)) +
        
        theme_bw(base_size = 15) + labs(y=expression(paste("Short Tandem\nDuplications"))) +
        gg_theme
      
      ,
      ggplot(stacks_df %>% filter(var == "SV5"),aes(y="",x=median_value)) + 
        
        geom_bar(stat="identity",fill="black") + 
        scale_x_continuous(limits = c(0,200)) +
        
        theme_bw(base_size = 15) + labs(y=expression(paste("Large\nDeletions"))) +
        gg_theme
      
      ,
      ggplot(stacks_df %>% filter(var == "hrd"),aes(y="",x=median_value)) + 
        
        geom_bar(stat="identity",fill="black") + 
        scale_x_continuous(limits = c(0,50)) +
        
        theme_bw(base_size = 15) + labs(y=expression(paste("Segments with Loss\nof Heterozygosity"))) +
        gg_theme
      
      ,
      ncol = 1, align = 'hv',axis = 'tbrl',rel_widths = c(1,1,1,1,1)
    
  )

weights_df <- boot[boot$var %in% c("del.mh.prop.w","SNV3.w","SV3.w","SV5.w","hrd.w"),]
intercept <- boot$median_value[boot$var == "intercept.w"]

#equation [4] in Davies et al. 2017
weights_df$probability <- 1 / ( 1 + exp(-(intercept + weights_df$median_value)))

weights_df$var_long[weights_df$var == "SV5.w"] <- "Large Deletions"
weights_df$var_long[weights_df$var == "SV3.w"] <- "Tandem Duplications"
weights_df$var_long[weights_df$var == "SNV3.w"] <- "SBS3"
weights_df$var_long[weights_df$var == "hrd.w"] <- "LOH"
weights_df$var_long[weights_df$var == "del.mh.prop.w"] <- "Microhomologous Deletions"

weights_df <- weights_df[order(weights_df$var_long,decreasing = T),]
weights_df$probability_cum <- cumsum(weights_df$probability)



hrd_color <- c("#000000", "#242424", "#999999" ,"#d2d2d2", "#e8e8e8")
out_path <- paste(work_dir, 'hrd.svg', sep='/')

svg(out_path, width = 8, height = 2.5, bg = "transparent")
print(
ggplot(weights_df ,aes(x="Sample",y=as.numeric(probability))) + 
  
  geom_bar(aes(fill=var_long),stat ="identity") + 
  
  annotate(x = 0, xend=2, y=cutoff_low, yend=cutoff_low, geom="segment",colour = "gray",linetype="dashed") +
  annotate(geom="text",x = 0,y=cutoff_low/2,color="gray30",label="HR-P", hjust = 0.5, vjust = -2,size=4) +
  
  annotate(geom="text",x = 0,y=(cutoff_high + max(hrd_median, 0.40))/2, color="gray30",label="HR-D", hjust = 0.5, vjust = -2,size=4) +
  
  scale_y_continuous( limit = c(0,1)) + 
  scale_fill_manual(values=hrd_color) +
  scale_color_manual(values=hrd_color) +
  
  guides(fill='none',color='none')+
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
    plot.title = element_text(hjust = 0.5)
  ) +
  geom_point(aes(y=as.numeric(probability_cum),x=c(1,1,1,1,1))) +
  
  geom_segment(aes(yend=as.numeric(probability_cum)*0.8+0.05,xend=c(1.7,1.5,1.3,1.5,1.7),y=as.numeric(probability_cum),x=c(1,1,1,1,1))) +
  geom_label(aes(label=var_long,y=as.numeric(probability_cum)*0.8+0.05,x=c(0.6,0.4,0.2,0.4,0.6)), vjust = -6, fill="white", label.padding = unit(3, "point"))+
  
  coord_flip() 
  #geom_text( aes(label = var),   vjust = -10, nudge_x = -0.4) 
)
dev.off()



  
    
  ggplot(boot[boot$var == "Probability.w",],aes(x="Sample")) + 
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
   #   line = element_blank(),
      panel.background = element_rect(fill = "transparent", colour = NA),
      plot.background = element_rect(fill="transparent",color=NA)
      
    ) 
  
txt <- paste(readLines(paste(work_dir,"hrd.svg",sep="/")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)
