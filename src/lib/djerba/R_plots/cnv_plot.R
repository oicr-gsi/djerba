#! /usr/bin/env Rscript
#centromeres from USCS
#http://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1334321853_hiXsRQvWI9Djbr8IrSABHWafymIR&clade=mammal&org=Human&db=hg38&hgta_group=map&hgta_track=centromeres&hgta_table=0&hgta_regionType=genome&position=chrX%3A15%2C560%2C138-15%2C602%2C945&hgta_outputType=primaryTable&hgta_outFileName=

library(dplyr)
library(tidyr)
library(optparse)
library(ggplot2)

option_list = list(
  make_option(c("-d", "--dir"), type="character", default=NULL, help="report directory path", metavar="character"),
  make_option(c("-s", "--segfile"), type="character", default=NULL, help="segments file", metavar="character"),
  make_option(c("-S", "--segfiletype"), type="character", default='sequenza', help="program that made the segments file, supported options are sequenza and purple", metavar="character"),
  make_option(c("-C", "--highCN"), type="integer", default=4, help="high copy number, for plot labelling", metavar="character")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)

segfiletype       <- opt$segfiletype
highCN            <- opt$highCN
segfile_path      <- opt$segfile
dir_path          <- opt$dir

#take in centromere data and process
data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')
centromeres_path <- paste(data_dir, 'hg38_centromeres.txt', sep='/')

centromeres <- read.table(centromeres_path,header=T)

centromeres <- separate(centromeres,chrom,c("blank","chr"),"chr",fill="left",remove = FALSE)
centromeres$Chr <- factor(c(centromeres$chr), levels = c(1:22,"X"))
centromeres <- centromeres %>% filter(!is.na(Chr))

chrom_order <- unique(centromeres$chrom[order(centromeres$Chr)])

centromeres_sub <- centromeres %>% dplyr::select(chromStart,chromEnd,chrom)
names(centromeres_sub) <- c("start.pos","end.pos","Chromosome")
centromeres_sub$A <- NA
centromeres_sub$B <- NA
centromeres_sub$CNt_high <- NA
centromeres_sub$CNt <- NA
centromeres_sub$cent <- 1

###take in segment file
segs <- read.table(segfile_path, sep = "\t", header = T, comment.char = "!")

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

segs$segment_class[ segs$segment_size >= 3 ] <- ">3Mb"
segs$segment_class[ segs$segment_size < 3 ] <- "<3Mb"
segs$CNt_high[segs$CNt > highCN] <- "high"

segs$Chromosome <-  factor(segs$chromosome, levels= chrom_order, ordered = T)

fittedSegmentsDF_sub <- segs %>% dplyr::select(start.pos,end.pos,A,B,CNt,CNt_high,Chromosome)
fittedSegmentsDF_sub$cent <- NA

fittedSegmentsDF_sub <- rbind.data.frame(fittedSegmentsDF_sub,centromeres_sub)

fittedSegmentsDF_sub$A_adj <- fittedSegmentsDF_sub$A + 0.1
fittedSegmentsDF_sub$B_adj <- fittedSegmentsDF_sub$B - 0.1

fittedSegmentsDF_sub <- separate(fittedSegmentsDF_sub,Chromosome,c("blank","chr"),"chr",fill="left",remove = FALSE)
fittedSegmentsDF_sub$Chr <- factor(c(fittedSegmentsDF_sub$chr), levels = c(1:22,"X"))

options(bitmapType='cairo')
svg(paste0(dir_path,"/seg_allele_plot.svg"), width = 8, height = 2)
print(
  
ggplot(fittedSegmentsDF_sub) + 
  geom_vline(aes(xintercept = start.pos,linetype=as.factor(cent)),color="lightgrey") +
  
  geom_segment(aes(x=start.pos, xend=end.pos, y=A_adj, yend=A_adj),color="#65bc45",size=2, na.rm = TRUE) + 
  geom_segment(aes(x=start.pos, xend=end.pos, y=B_adj, yend=B_adj),color="#0099ad",size=2, na.rm = TRUE) + 
  
  geom_point(aes(x=start.pos,y=4.1,shape=CNt_high),size=1) +
  
  facet_grid(.~Chr,scales = "free",space="free", switch="both")+ 

  guides(shape='none',alpha='none',linetype='none') +
  labs(y="Copy Number") + 
  ylim(-0.11,4.11) +
  scale_shape_manual(values=c(17),labels=": CN>4",name="",na.translate = F) +
  
  theme_bw() + 
  theme(axis.title.x=element_blank(),
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

svg(paste0(dir_path,"/seg_CNV_plot.svg"), width = 8, height = 1.5)
print(
  
ggplot(fittedSegmentsDF_sub) + 
  geom_vline(aes(xintercept = start.pos,linetype=as.factor(cent)),color="lightgrey") +
  
  geom_segment(aes(x=start.pos, xend=end.pos, y=CNt, yend=CNt),color="black",size=2, na.rm = TRUE) + 

  geom_point(aes(x=start.pos,y=4.1,shape=CNt_high),size=1) +
  
  facet_grid(.~Chr,scales = "free",space="free", switch="both")+ 
  
  guides(shape='none',alpha='none',linetype='none') +
  labs(y="Copy Number") + 
  ylim(-0.11,4.11) +
  scale_shape_manual(values=c(17)) +
  
  theme_bw() + 
  theme(axis.title.x=element_blank(),
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



