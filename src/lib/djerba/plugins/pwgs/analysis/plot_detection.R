#! /usr/bin/env Rscript

library(optparse)
library(ggplot2)

options(scipen=999)
options(digits = 5)

# get options
option_list = list(
  make_option(c("-r", "--hbc_results"), type="character", default=NULL, help="results file path", metavar="character"),
  make_option(c("-o", "--output_directory"), type="character", default="./", help="results file path", metavar="character"),
  make_option(c("-p", "--pval"), type="numeric", default=3.15e-5, help="p-value cutoff", metavar="numeric")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

results_path <- opt$hbc_results
output_directory <- opt$output_directory
pval_cutoff <- opt$pval

## intake
results <- read.csv(results_path,header=TRUE)
results$label <- "CONTROLS"
results$label[1] <- "THIS SAMPLE"

mean_detection <- mean(results$sites_detected[results$label == "CONTROLS"])

results_cov <- results

dataset_cutoff <- (qnorm(pval_cutoff,lower.tail = F) * sd(results_cov$sites_detected)) +  mean(results_cov$sites_detected)

##plot
options(bitmapType='cairo')
svg(paste0(output_directory,"pWGS.svg"), width = 5, height = 1.2)
    
ggplot(results_cov) + 
    geom_jitter(aes(x=0,y=sites_detected,color=label,size=label,shape=label),width = 0.01) +
    
    geom_hline(yintercept = 0,alpha=0.25,color="white")  +
    
    annotate(x = -0.1, xend=0.1, y=dataset_cutoff, yend=dataset_cutoff,
             geom="segment",linetype="dashed",
             colour = "red") +
    
    annotate(geom="text",y = dataset_cutoff,x=0,color="red",label="Detection Cutoff", hjust = 1.1, vjust = 3,size=2.5) +
    annotate(geom="text",y = mean_detection,x=0,color="gray",label="Controls", hjust = 0.5, vjust = -4,size=2.5) +
    annotate(geom="text",y = results$sites_detected[1],x=0,color="black",label="This Sample", hjust = 0.8, vjust = -3,size=2.5) +
  
    labs(x="",y="Sites Detected",color="",title="",shape="",size="") +
    scale_color_manual( values= c( "gray", "black") ) +
    scale_shape_manual(values=c(1,13)) +
    theme_classic() +
    guides(shape=FALSE,size=FALSE,color=FALSE)+
    theme(
      panel.grid.major = element_blank(), 
      panel.grid.minor = element_blank(),
      text = element_text(size = 9),
      legend.title=element_blank(),
      plot.margin = unit(c(0, 0, 0, 0), "lines"),
      axis.title.y=element_blank(),
      axis.text.y=element_blank(),
      axis.ticks.y=element_blank()
    ) + 
    coord_flip(clip = "off", xlim=c(-0.1,0.1)) 
  
dev.off()
     
txt <- paste(readLines(paste0(output_directory,"pWGS.svg")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)


