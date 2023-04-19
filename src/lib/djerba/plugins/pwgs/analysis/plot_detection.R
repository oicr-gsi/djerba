#! /usr/bin/env Rscript

library(optparse)
library(ggplot2)
'%ni%' <- function(x,y)!('%in%'(x,y))

options(scipen=999)
options(digits = 5)

# get options
option_list = list(
  make_option(c("-r", "--hbc_results"), type="character", default=NULL, help="results file path", metavar="character"),
  make_option(c("-v", "--vaf_results"), type="character", default=NULL, help="vaf file path", metavar="character"),
  make_option(c("-o", "--output_directory"), type="character", default="./", help="results file path", metavar="character"),
  make_option(c("-p", "--pval"), type="numeric", default=3.15e-5, help="p-value cutoff", metavar="numeric")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

results_path <- opt$hbc_results
vaf_path <- opt$vaf_results
output_directory <- opt$output_directory
pval_cutoff <- opt$pval

##test
results_path <- opt$hbc_results
vaf_path <- opt$vaf_results
output_directory <- opt$output_directory
pval_cutoff <- opt$pval

## intake
vaf <- read.table(vaf_path,header = T)
sample_coverage = median(vaf$goodreads)

results <- read.csv(results_path,header=TRUE)
results$label <- "CONTROLS"
results$label[1] <- "THIS SAMPLE"

mean_detection <- mean(results$sites_detected[results$label == "CONTROLS"])
sites_checked <- results$sites_checked[results$label == "THIS SAMPLE"]

results_cov <- results
results_cov$noise_rate <- results_cov$sites_detected / results_cov$median_coverage
results_cov$noise <- results_cov$noise_rate * sample_coverage

dataset_cutoff <- ( qnorm(pval_cutoff,lower.tail = F) * sd(results_cov$noise[results$label == "CONTROLS"]) ) +  mean(results_cov$noise[results$label == "CONTROLS"])

rep_length = round(log(sites_checked,10),0)
my_breaks <- rep(1:9, rep_length) * (10^rep(0:(rep_length-1), each = 9))

my_labels <- my_breaks
my_labels[my_labels %ni%  10^(0:round(log(sites_checked,10),0))] <- ""

my_breaks[length(my_breaks)] <- sites_checked
my_labels[length(my_labels)] <- sites_checked
 
##plot
options(bitmapType='cairo')
svg(paste0(output_directory,"pWGS.svg"), width = 5, height = 1.2)
    
ggplot(results_cov[results$label == "CONTROLS",]) + 
    geom_jitter(aes(x=0,y=noise,color=label,shape=label),width = 0.01) +
    
    geom_hline(yintercept = 0,alpha=0.25,color="white")  +
   geom_hline(yintercept = sites_checked,alpha=0.25,color="white")  +
  
    annotate(x = -0.1, xend=0.1, y=dataset_cutoff, yend=dataset_cutoff,
             geom="segment",linetype="dashed",
             colour = "black") +
    
    annotate(geom="text",y = dataset_cutoff,x=0,color="black",label="Detection Cutoff",  vjust = -4,size=2.5) +
    annotate(geom="text",y = mean_detection,x=0,color="gray30",label="Controls", hjust = 0.5, vjust = 3,size=2.5) +
    annotate(geom="text",y = results$sites_detected[1],x=0,color="red",label="This Sample",  vjust = -2.5,size=2.5) +
  annotate(geom="point",y = results$sites_detected[1],x=0,color="red",shape=1, size=5) +
  annotate(geom="point",y = results$sites_detected[1],x=0,color="red",shape=20, size=1.5) +
  
    labs(x="",y="Sites Detected",color="",title="",shape="",size="") +
    scale_color_manual( values= c( "gray30", "red") ) +
    scale_shape_manual(values=c(16,1)) +
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
 scale_y_continuous(trans = "log10",
                    breaks = my_breaks,
                    labels = my_labels
                    ) +
    coord_flip(clip = "off", xlim=c(-0.1,0.1)) 
  
dev.off()
     
txt <- paste(readLines(paste0(output_directory,"pWGS.svg")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)


