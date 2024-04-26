#! /usr/bin/env Rscript

library(optparse)
library(ggplot2)

'%ni%' <- function(x,y)!('%in%'(x,y))

process_results <- function(results, sample_coverage){
  results$label <- "CONTROLS"
  results$label[1] <- "THIS SAMPLE"
  results$noise_rate <- results$sites_detected / results$median_coverage
  results$noise <- results$noise_rate * sample_coverage
  return(results)
}

get_mrd_stats <- function(results, pval_cutoff){
  zscore <- (results$noise[results$label == "THIS SAMPLE"] - mean(results$noise))/ sd(results$noise)
  pvalue <- pnorm(zscore,lower.tail=F)
  dataset_cutoff <- (qnorm(pval_cutoff,lower.tail = F) * sd(results$noise)) +  mean(results$noise[results$label == "CONTROLS"])

  mrd_stats <- list(
    "zscore" = zscore,
    "pvalue" = pvalue,
    "dataset_cutoff" = dataset_cutoff,
    "sites_checked" =  results$sites_checked[results$label == "THIS SAMPLE"],
    "mean_detection" = mean(results$sites_detected[results$label == "CONTROLS"])
  )
  return(mrd_stats)
}

options(scipen=999)
options(digits = 5)

# get options
option_list = list(
  make_option(c("-r", "--hbc_results"), type="character", default=NULL, help="results file path", metavar="character"),
  make_option(c("-v", "--vaf_results"), type="character", default=NULL, help="vaf file path", metavar="character"),
  make_option(c("-o", "--output_directory"), type="character", default="./", help="results file path", metavar="character"),
  make_option(c("-p", "--pval"), type="numeric", default=3.29e-5, help="p-value cutoff", metavar="numeric")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

results_path <- opt$hbc_results
vaf_path <- opt$vaf_results
output_directory <- opt$output_directory
pval_cutoff <- opt$pval

## intake
vaf <- read.table(vaf_path,header = T)
sample_coverage = median(vaf$goodreads)

results_raw <- read.csv(results_path, header=T)
results <- process_results(results_raw, sample_coverage)
mrd_stats <- get_mrd_stats(results, pval_cutoff)

mean_detection <- mrd_stats$mean_detection
sites_checked  <- mrd_stats$sites_checked
dataset_cutoff <- mrd_stats$dataset_cutoff


##plot
rep_length = round(log(sites_checked,10),0)
my_breaks <- rep(1:9, rep_length) * (10^rep(0:(rep_length-1), each = 9))

my_labels <- my_breaks
my_labels[my_labels %ni% 10^(0:round(log(sites_checked,10),0))] <- ""

my_breaks[length(my_breaks)] <- sites_checked
my_labels[length(my_labels)] <- sites_checked

my_labels[14] <- "Sites Detected:" 

options(bitmapType='cairo')
svg(paste(output_directory,"pWGS.svg",sep="/"), width = 5, height = 1)

ggplot(results[results$label == "CONTROLS",]) + 
    geom_boxplot(aes(x=0,y=noise,color=label,shape=label),width = 0.05, outlier.shape = NA) +
    
    geom_hline(yintercept = 1,alpha=0.25,color="white")  +
    geom_hline(yintercept = sites_checked,alpha=0.25,color="white")  +
  
    annotate( geom="segment", x = -0.1, xend=0.1, y=dataset_cutoff, yend=dataset_cutoff, colour = "gray") +
    
    annotate(geom="text",y = dataset_cutoff,x=0,color="gray30",label=paste("Detection Cutoff:", round(dataset_cutoff, 2)," reads"),  vjust = -4.5, size=2.5) +
    annotate(geom="text",y = mean_detection, x=0,color="black",label="Control Cohort", hjust = 0.3, vjust = 3, size=2.5) +
    annotate(geom="text",y = results$sites_detected[1],x=0,color="red",label=paste("This Sample:",round(results$sites_detected[1])," reads"),  vjust = -2.5,size=2.5) +
   
    annotate(geom="point",y = results$sites_detected[1],x=0,color="red",shape=1, size=5) +
    annotate(geom="point",y = results$sites_detected[1],x=0,color="red",shape=20, size=1.5) +
  
    labs(x="",y="",color="",title="",shape="",size="") +
    scale_color_manual( values= c( "gray30", "red") ) +
    scale_shape_manual(values=c(16,1)) +
    theme_classic() +
    guides(shape="none",size="none",color="none")+
    theme(
      axis.line.y = element_blank(),
      panel.grid.major = element_blank(), 
      panel.grid.minor = element_blank(),
      text = element_text(size = 9),
      legend.title=element_blank(),
      plot.margin = unit(c(0, 0, 0, 0), "lines"),
      axis.title=element_blank(),
      axis.text.y=element_blank(),
      axis.ticks.y=element_blank()
    ) + 
 scale_y_continuous(trans = "log10",
                    breaks = my_breaks,
                    labels = my_labels,
                    limits = c(40, sites_checked)
                    ) +
    coord_flip(clip = "off") 
  
dev.off()
     
txt <- paste(readLines(paste(output_directory,"pWGS.svg",sep="/")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)


