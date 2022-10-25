#! /usr/bin/env Rscript

library(dplyr)
library(tidyr)
library(optparse)
library(ggplot2)

option_list = list(
  make_option(c("-c", "--centromeres"), type="character", default='~/Documents/data/hg38_centromeres.txt', help="centromeres file", metavar="character"),
  make_option(c("-s", "--segfile"), type="character", default=NULL, help="segments file", metavar="character")
)

#centromeres from USCS
#http://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1334321853_hiXsRQvWI9Djbr8IrSABHWafymIR&clade=mammal&org=Human&db=hg38&hgta_group=map&hgta_track=centromeres&hgta_table=0&hgta_regionType=genome&position=chrX%3A15%2C560%2C138-15%2C602%2C945&hgta_outputType=primaryTable&hgta_outFileName=
centromeres <- read.table('~/Documents/data/hg38_centromeres.txt',header=T)

centromeres <- separate(centromeres,chrom,c("blank","chr"),"chr",fill="left",remove = FALSE)
centromeres$Chr <- factor(c(centromeres$chr), levels = c(1:22,"X"))
centromeres <- centromeres %>% filter(!is.na(Chr))

chrom_order <- unique(centromeres$chrom[order(centromeres$Chr)])

centromeres_sub <- centromeres %>%   dplyr::select(chromStart,chromEnd,chrom)
names(centromeres_sub) <- c("start.pos","end.pos","Chromosome")
centromeres_sub$A <- NA
centromeres_sub$B <- NA
centromeres_sub$CNt_high <- NA
centromeres_sub$CNt <- NA
centromeres_sub$cent <- 1

#Segments file
setwd('/Volumes/')

#sample = "OCT_010707_Bn_M"
#Dir = "cgi/scratch/fbeaudry/hartwig/purple/OCT_010707/500"
#segs_purp = read.table(file = paste0(Dir, "/", sample, ".purple.segment.tsv"), sep = "\t", header = T, comment.char = "!")

#sample="PANX_1385_Lv_M"
#Dir="cgi/cap-djerba/PASS01/PANX_1385/gammas/500"
#segs_seq <- read.table(paste0(Dir, "/", sample, "_WG_100-NH-017_LCM4_6_segments.txt"), sep = "\t", header = T, comment.char = "!")

sample="BTC_0013_Lv_P"
Dir="cgi/scratch/fbeaudry/djerba_test/BTC_0013/gammas/400"
segs_seq <- read.table(paste0(Dir, "/", sample, "_WG_HPB-199_LCM_segments.txt"), sep = "\t", header = T, comment.char = "!")

##
#end.pos

#####
fittedSegmentsDF <- segs_seq

## Bf = minorAllele_fz
# end.pos = end
# start.pos = start


#fittedSegmentsDF$minorAllele_fz <- 1 - fittedSegmentsDF$tumorBAF
##filter negatives ?

fittedSegmentsDF$segment_size <- (fittedSegmentsDF$end.pos - fittedSegmentsDF$start.pos)/1000000
fittedSegmentsDF$segment_class[ fittedSegmentsDF$segment_size >= 3 ] <- ">3Mb"
fittedSegmentsDF$segment_class[ fittedSegmentsDF$segment_size < 3 ] <- "<3Mb"
#fittedSegmentsDF$bafCountNA <- fittedSegmentsDF$bafCount
#fittedSegmentsDF$bafCountNA[fittedSegmentsDF$bafCountNA == 0]<- NA

fittedSegmentsDF$CNt_high[fittedSegmentsDF$CNt > 4] <- "high"

fittedSegmentsDF$Chromosome <-  factor(fittedSegmentsDF$chromosome, levels= chrom_order, ordered = T)

fittedSegmentsDF_sub <- fittedSegmentsDF %>% dplyr::select(start.pos,end.pos,A,B,CNt,CNt_high,Chromosome)
fittedSegmentsDF_sub$cent <- NA


fittedSegmentsDF_sub <- rbind.data.frame(fittedSegmentsDF_sub,centromeres_sub)

fittedSegmentsDF_sub$A_adj <- fittedSegmentsDF_sub$A + 0.1
fittedSegmentsDF_sub$B_adj <- fittedSegmentsDF_sub$B - 0.1

fittedSegmentsDF_sub <- separate(fittedSegmentsDF_sub,Chromosome,c("blank","chr"),"chr",fill="left",remove = FALSE)
fittedSegmentsDF_sub$Chr <- factor(c(fittedSegmentsDF_sub$chr), levels = c(1:22,"X"))

options(bitmapType='cairo')
svg("cgi/scratch/fbeaudry/djerba_test/BTC_0013/CNV_allele_plot.svg", width = 8, height = 2)
print(
  
ggplot(fittedSegmentsDF_sub) + 
  geom_vline(aes(xintercept = start.pos,linetype=as.factor(cent)),color="lightgrey") +
  
  geom_segment(aes(x=start.pos, xend=end.pos, y=A_adj, yend=A_adj),color="#65bc45",size=2, na.rm = TRUE) + 
  geom_segment(aes(x=start.pos, xend=end.pos, y=B_adj, yend=B_adj),color="#0099ad",size=2, na.rm = TRUE) + 
  
  geom_point(aes(x=start.pos,y=4.1,shape=CNt_high),size=1) +
  
  facet_grid(.~Chr,scales = "free",space="free", switch="both")+ 

  guides(alpha='none',linetype='none') +
  labs(y="Copy Number") + 
  ylim(-0.11,4.11) +
  scale_shape_manual(values=c(17),labels=": CN>4",name="",na.translate = F) +
  
  theme_bw() + 
  # scale_y_continuous(limits = c(0, 8), breaks = seq(0, 8, by = 1)) +
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        panel.spacing.x=unit(2, "points"),
        panel.grid.minor = element_blank(),
        panel.grid.major = element_blank(),
        strip.background = element_blank(),
        text = element_text(size = 10),
        plot.margin = unit(c(2, 2, 2, 2), "points"),
        legend.position="top",
        legend.text=element_text(size=12)
        ) 

)
dev.off()

svg("cgi/scratch/fbeaudry/CNV_plot.svg", width = 8, height = 1.5)
print(
  
ggplot(fittedSegmentsDF_sub) + 
  geom_vline(aes(xintercept = start.pos,linetype=as.factor(cent)),color="lightgrey") +
  
  geom_segment(aes(x=start.pos, xend=end.pos, y=CNt, yend=CNt),color="black",size=2, na.rm = TRUE) + 

  geom_point(aes(x=start.pos,y=4.1,shape=CNt_high),size=2) +
  
  facet_grid(.~Chr,scales = "free",space="free", switch="both")+ 
  
  guides(shape='none',alpha='none',linetype='none') +
  labs(y="Copy Number") + 
  ylim(-0.11,4.11) +
  scale_shape_manual(values=c(17)) +
  
  theme_bw() + 
  # scale_y_continuous(limits = c(0, 8), breaks = seq(0, 8, by = 1)) +
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



