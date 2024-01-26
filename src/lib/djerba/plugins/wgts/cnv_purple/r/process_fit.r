#! /usr/bin/env Rscript

library(optparse)

plot_purity_range <- function(rangeDF){
  #forked from hmftools/purple/src/main/resources/r/copyNumberPlots.R on Aug 19th 2022
  
  library(ggplot2)
  library(dplyr)
  
  bestPurity = rangeDF[1, "purity"]
  bestPloidy = rangeDF[1, "ploidy"]
  bestScore = rangeDF[1, "score"]
  
  range_after =  rangeDF %>%
    arrange(purity, ploidy) %>%
    group_by(purity) %>%
    mutate(
      absScore = pmin(4, score),
      score = pmin(1, abs(score - bestScore) / score),
      leftPloidy = lag(ploidy),
      rightPloidy = lead(ploidy),
      xmin = ploidy - (ploidy - leftPloidy) / 2,
      xmax = ploidy + (rightPloidy - ploidy) / 2,
      ymin = purity - 0.005,
      ymax = purity + 0.005,
      xmin = ifelse(is.na(xmin), ploidy, xmin),
      xmax = ifelse(is.na(xmax), ploidy, xmax))
  
  maxPloidy = min(range_after %>% arrange(purity, -ploidy) %>% group_by(purity)  %>% filter(row_number() == 1) %>% select(purity, ploidy = xmax) %>% ungroup() %>% select(ploidy))
  minPloidy = max(range_after %>% arrange(purity, ploidy) %>% group_by(purity)  %>% filter(row_number() == 1) %>% select(purity, maxPloidy = xmin) %>% ungroup() %>% select(maxPloidy))
  
  maxPloidy = max(maxPloidy, bestPloidy)
  minPloidy = min(minPloidy, bestPloidy)
  
  range_after = range_after %>%
    filter(xmin <= maxPloidy, xmax >= minPloidy) %>%
    mutate(xmax = pmin(xmax, maxPloidy), xmin = pmax(xmin, minPloidy))
  
  
  range_plot <- ggplot(range_after) +
    geom_rect(aes(fill=score, xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax)) +
    
    geom_segment(aes(y = 0.085, yend = 1.05, x=bestPloidy, xend = bestPloidy), linetype = "dashed", linewidth = 0.1) +
    geom_label(data = data.frame(), aes(x = bestPloidy, y = 1.05, label = round(bestPloidy, 2)), size = 5) +
    geom_segment(aes(y = bestPurity, yend = bestPurity, x=minPloidy, xend = maxPloidy + 0.4), linetype = "dashed", linewidth = 0.1) +
    geom_label(data = data.frame(), aes(y = bestPurity, x = maxPloidy + 0.4, label = paste0(bestPurity*100,"%" )), size = 5, hjust = 0.7) +
    
    
    scale_y_continuous(labels = c("30%", "50%", "75%", "100%"), breaks = c(0.3, 0.5, 0.75, 1)) +
    scale_fill_gradientn(colours=c("black","darkblue","blue", "lightblue",  "white", "white"), limits = c(0, 1), values=c(0,0.1, 0.1999, 0.2, 0.5, 1), breaks = c(0.1,0.25, 0.5, 1), labels = c("10%","25%", "50%", "100%"), name = "Relative\nScore") +
    xlab("Ploidy") + ylab("Cellularity") + theme_bw(base_size=18) +
    theme(panel.grid = element_blank()) 
  
  return(range_plot)
  
}

options(bitmapType='cairo')

option_list = list(
  make_option(c("-d", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-r", "--range_file"), type="character", default=NULL, help="purity range file", metavar="character")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
argv <- parse_args(opt_parser)

dir_path   <- argv$outdir
range_file <- argv$range_file

rangeDF = read.table(file = range_file, sep = "\t", header = T, comment.char = "!") 

purity_plot <- plot_purity_range(rangeDF)

svg(paste0(dir_path,"/purple.range.svg"), width = 8, height = 7)
print(purity_plot)
dev.off()

write.table(rangeDF, file=paste0(dir_path, "/purple.range.txt"), sep="\t", row.names=FALSE, quote=FALSE)

