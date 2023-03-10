#! /usr/bin/env Rscript

library(dplyr)
library(tidyr)
library(optparse)
library(ggplot2)

process_centromeres <- function(centromeres_path){
  centromeres <- read.table(centromeres_path,header=T)
  centromeres <- separate(centromeres,chrom,c("blank","chr"),"chr",fill="left",remove = FALSE)
  centromeres$Chr <- factor(c(centromeres$chr), levels = c(1:22,"X"))
  centromeres <- centromeres %>% filter(!is.na(Chr))
  
  centromeres_sub <- centromeres %>% dplyr::select(chromStart,chromEnd,Chr)
  names(centromeres_sub) <- c("start.pos","end.pos","Chromosome")
  centromeres_sub$A <- NA
  centromeres_sub$B <- NA
  centromeres_sub$CNt_high <- NA
  centromeres_sub$CNt <- NA
  centromeres_sub$cent <- 1
  return(centromeres_sub)
}

data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')
centromeres_path <- paste(data_dir, 'hg38_centromeres.txt', sep='/')

chromosomes_incl <- c(1:22,"X")
options(bitmapType='cairo')

## parse input
option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="report directory path", metavar="character"),
  make_option(c("-s", "--segfile"), type="character", default=NULL, help="allele specific segments file (e.g. aratio_segments.txt)", metavar="character"),
  make_option(c("-S", "--segfiletype"), type="character", default='sequenza', help="program that made the segments file, supported options are sequenza and purple", metavar="character")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

segfiletype       <- opt$segfiletype
segfile_path      <- opt$segfile
dir_path          <- opt$dir

##test
#segfile_path <- "/Volumes/cgi/scratch/fbeaudry/djerba_test/PANX_1394/report/aratio_segments.txt"
#centromeres_path <- "/Volumes/cgi/scratch/fbeaudry/djerba/src/lib/djerba/data/hg38_centromeres.txt"


##process segment file
segs <- read.table(segfile_path, sep = "\t", header = T, comment.char = "!")
segs <- separate(segs,chromosome,c("blank","chr"),"chr",fill="left",remove = FALSE)

if(segfiletype == 'purple'){
  
  print("PURPLE support is not yet enabled")
  # Bf = minorAllele_fz
  # end.pos = end
  # start.pos = start
  #segs$minorAllele_fz <- 1 - segs$tumorBAF
  
  ##filter negatives ?
  #segs$bafCountNA <- segs$bafCount
  #segs$bafCountNA[segs$bafCountNA == 0]<- NA
  
} else if(segfiletype == 'sequenza'){ 
  
  segs$segment_size <- (segs$end.pos - segs$start.pos)/1000000
  
} else {
  print('unsupported segment file type/software')
}

#highCN <- max(segs$CNt[ segs$segment_size >= 3 ] )
highCN <- 8
segs$CNt_high[segs$CNt > highCN] <- "high"

segs$Chromosome <-  factor(segs$chr, levels= chromosomes_incl, ordered = T)

fittedSegmentsDF_sub <- segs %>% dplyr::select(start.pos,end.pos,A,B,CNt,CNt_high,Chromosome)
fittedSegmentsDF_sub$cent <- NA

fittedSegmentsDF_sub <- rbind.data.frame(
                          fittedSegmentsDF_sub,
                          process_centromeres(centromeres_path)
                        )

## Copy Number Plot
y_highCN <- highCN

svg(paste0(dir_path,"/seg_CNV_plot.svg"), width = 8, height = 1.5)
  print(
    
    ggplot(fittedSegmentsDF_sub) + 
      
      geom_hline(yintercept = 2,color="lightgrey",linetype="dotted")+
      
      facet_grid(.~Chromosome,scales = "free",space="free", switch="both")+ 
      geom_point(aes(x=start.pos,y=y_highCN+0.25,shape=CNt_high),size=1) +
      
      geom_segment(aes(x=start.pos, xend=end.pos, y=CNt, yend=CNt),color="black",size=2, na.rm = TRUE) + 
      
      geom_vline(aes(xintercept = start.pos,linetype=as.factor(cent)),color="lightgrey")  +
      
      guides(shape='none',alpha='none',linetype='none') +
      labs(y="Copy Number") + 
      scale_shape_manual(values=c(17)) +
      
      scale_y_continuous(limits=c(-0.11,y_highCN+0.3),breaks=seq(0,y_highCN,by=2)) + 
      theme_bw() + 
      theme(
        axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        panel.spacing.x=unit(2, "points"),
        panel.grid.minor = element_blank(),
        panel.grid.major = element_blank(),
        strip.background = element_blank(),
        text = element_text(size = 10),
        plot.margin = unit(c(2, 2, 2, 2), "points")
      ) 
    
  )
dev.off()

## Allele-specific
fittedSegmentsDF_sub$A_adj <- fittedSegmentsDF_sub$A + 0.1
fittedSegmentsDF_sub$B_adj <- fittedSegmentsDF_sub$B - 0.1

svg(paste0(dir_path,"/seg_allele_plot.svg"), width = 8, height = 2)
print(
  
  ggplot(fittedSegmentsDF_sub) + 
    geom_vline(aes(xintercept = start.pos,linetype=as.factor(cent)),color="lightgrey") +
    
    geom_segment(aes(x=start.pos, xend=end.pos, y=A_adj, yend=A_adj),color="#65bc45",size=2, na.rm = TRUE) + 
    geom_segment(aes(x=start.pos, xend=end.pos, y=B_adj, yend=B_adj),color="#0099ad",size=2, na.rm = TRUE) + 
    
    geom_point(aes(x=start.pos,y=highCN+0.1,shape=CNt_high),size=1) +
    
    facet_grid(.~Chromosome,scales = "free",space="free", switch="both")+ 
    
    guides(shape='none',alpha='none',linetype='none') +
    labs(y="Copy Number") + 
    ylim(-0.11,highCN+0.11) +
    scale_shape_manual(values=c(17),labels=": CN>4",name="",na.translate = F) +
    
    theme_bw() + 
    theme(
      axis.title.x=element_blank(),
      axis.text.x=element_blank(),
      axis.ticks.x=element_blank(),
      panel.spacing.x=unit(2, "points"),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_blank(),
      strip.background = element_blank(),
      text = element_text(size = 10),
      plot.margin = unit(c(2, 2, 2, 2), "points"),
      legend.text=element_text(size=12)
    ) 
  
)
dev.off()


