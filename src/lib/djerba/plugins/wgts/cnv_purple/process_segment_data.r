#! /usr/bin/env Rscript

library(dplyr)
library(tidyr)
library(optparse)
library(ggplot2)

chromosomes_incl <- c(1:22,"X")
options(bitmapType='cairo')
basedir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), sep='/')
source(paste0(basedir, "/plugins/wgts/cnv_purple/CNA_supporting_functions.r"))

## parse input
option_list = list(
  make_option(c("-d", "--outdir"), type="character", default=NULL, help="report directory path", metavar="character"),
  make_option(c("-s", "--segfile"), type="character", default=NULL, help="segments file ", metavar="character"),
  make_option(c("-c", "--centromeres"), type="character", default='sequenza', help="path to centromeres file", metavar="character"),
  make_option(c("-a", "--highCN"), type="character", default=6, help="High copy number (top of y-axis)", metavar="character")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

segfile_path      <- opt$segfile
dir_path          <- opt$outdir
centromeres_path  <- opt$centromeres
highCN            <- as.numeric(opt$highCN)
baf.min           <- 25


#### arm-level events ####
segs <- read.delim(segfile_path, header=TRUE) # segmented data already
segs <- segs[segs$bafCount > baf.min ,]

centromeres <- read.table(centromeres_path,header=T)

arm_level_calls <- arm_level_caller_purple(segs, centromeres, gain_threshold=highCN, shallow_deletion_threshold=-2)
write.table(arm_level_calls,file=paste0(dir_path, "/purple.arm_level_calls.txt"), sep="\t", row.names=FALSE, quote=FALSE, col.names = FALSE)

segs$ID <- "purple"
log2 <- segs[,c("ID","chromosome","start","end","bafCount")]
names(log2) <- c("ID",	"chrom"	,"loc.start"	,"loc.end"	,"num.mark")
log2$seg.mean <- log(segs$copyNumber/2, 2)
write.table(log2,file=paste0(dir_path, "/purple.seg"), sep="\t", row.names=FALSE, quote=FALSE, col.names = FALSE)

#### segment plot ####
segs <- separate(segs, chromosome,c("blank","chr"),"chr",fill="left",remove = FALSE)
segs$Chromosome <-  factor(segs$chr, levels= chromosomes_incl, ordered = T)

segs$CNt_high[segs$chrom > highCN] <- "high"


fittedSegmentsDF_sub <- segs %>% dplyr::select(start,end,Chromosome,majorAlleleCopyNumber,minorAlleleCopyNumber,copyNumber,CNt_high)
fittedSegmentsDF_sub$cent <- NA

fittedSegmentsDF_sub <- rbind.data.frame(
                          fittedSegmentsDF_sub,
                          process_centromeres(centromeres_path)
                        )

## Copy Number Plot
y_highCN <- highCN

svg(paste0(dir_path,"/purple.seg_CNV_plot.svg"), width = 8, height = 1.5)
  print(
    
    ggplot(fittedSegmentsDF_sub) + 
      
      geom_hline(yintercept = 2,color="lightgrey",linetype="dotted")+
      
      facet_grid(.~Chromosome,scales = "free",space="free", switch="both")+ 
      geom_point(aes(x=start,y=y_highCN+0.35,shape=CNt_high),size=1) +
      
      geom_segment(aes(x=start, xend=end, y=round(copyNumber), yend=round(copyNumber)),color="black",linewidth=2, na.rm = TRUE) + 
      
      geom_vline(aes(xintercept = start,linetype=as.factor(cent)),color="lightgrey")  +
      
      guides(shape='none',alpha='none',linetype='none') +
      labs(y="Copy Number") + 
      scale_shape_manual(values=c(17)) +
      
      scale_y_continuous(limits=c(-0.11,y_highCN+0.4),breaks=seq(0,y_highCN,by=2)) + 
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
fittedSegmentsDF_sub$A_adj <- fittedSegmentsDF_sub$majorAlleleCopyNumber + 0.1
fittedSegmentsDF_sub$B_adj <- fittedSegmentsDF_sub$minorAlleleCopyNumber - 0.1

svg(paste0(dir_path,"/purple.seg_allele_plot.svg"), width = 8, height = 2)
print(
  
  ggplot(fittedSegmentsDF_sub) + 
    geom_vline(aes(xintercept = start,linetype=as.factor(cent)),color="lightgrey") +
    
    geom_segment(aes(x=start, xend=end, y=A_adj, yend=A_adj),color="#65bc45",linewidth=2, na.rm = TRUE) + 
    geom_segment(aes(x=start, xend=end, y=B_adj, yend=B_adj),color="#0099ad",linewidth=2, na.rm = TRUE) + 
    
    geom_point(aes(x=start,y=highCN+0.1,shape=CNt_high),size=1) +
    
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


txt <- paste(readLines(paste0(dir_path,"/purple.seg_CNV_plot.svg")), collapse = "")
b64txt <- paste0("data:image/svg+xml;base64,", base64enc::base64encode(charToRaw(txt)))
print(b64txt)