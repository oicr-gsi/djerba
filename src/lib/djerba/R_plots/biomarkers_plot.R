library(ggplot2)

args = commandArgs(trailingOnly=TRUE)
directory <- args[1]

file <- paste0(directory,"msi.txt")

##test##
#setwd('/Volumes/')
#file <- 'cgi/scratch/fbeaudry/msi_test/BTC_0013/BTC_0013_Lv_P_WG_HPB-199_LCM.filter.deduped.realigned.recalibrated.msi.booted'

boot <- read.table(file)

names(boot) <- c("q0","q1","median","q3","q4")
boot$Sample <- "Sample"

jpeg(paste0("~/","msi.jpeg"), width = 500, height = 90,type="cairo") #
#svg(paste0("~/","msi.svg"), width = 5, height = 1.5,type="cairo") 

ggplot(msi_boot,
       aes(x="Sample")) + 
 # geom_vline(xintercept = 3.5,color="grey",linetype="dotted")+

  #geom_point(aes(x=point), shape=4, size=6) + 
  geom_bar(aes(y=median,fill=ifelse(median < 5,'red','green')),stat ="identity") + 
  geom_errorbar(aes(ymin=q1, ymax=q3), width=0,size=2) +
  geom_errorbar(aes(ymin=q0, ymax=q4), width=0) +
  
  geom_hline(yintercept = 5,color=ifelse(msi_boot$median < 5,'black','white'))+
  guides(fill=FALSE)+
  theme_bw(base_size=15) + 
  labs(x="",title="MSS                                                                               MSI",y="unstable microsatellites (%)") + 
  ylim(0,100) + guides(alpha="none")+
  
  scale_color_manual(values=c("#65bc45","#000000","#0099ad")) +
  theme(axis.text.y = element_text(angle = 90, vjust = 0.5, hjust=.5)) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank()) +
  theme(axis.title.y=element_blank(),
    axis.text.y=element_blank(),
    axis.ticks.y=element_blank())  + coord_flip()

dev.off()

