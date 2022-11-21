#install packages in console by > install.packages("<name>")
library(ggplot2)
library(data.table)
library(forcats) # within tidyverse

#SCATTER PLOT - callvcov####
callvcov_file = '/home/ltoy/Desktop/couch/extract/graph/compare_Callability (%)&Coverage (mean).csv'
callvcov <- fread(callvcov_file, header=TRUE)
callability = callvcov$`Callability (%)`
coverage = callvcov$`Coverage (mean)`

c<-ggplot(callvcov, aes(x=coverage, y=callability)) +
  geom_point(size=2, shape=18) +
  labs(x="Coverage (mean)", y="Callability (%)") +
  geom_smooth() 
ggsave("/home/ltoy/Desktop/couch/extract/callvcov.png", c, width=8,height=5)

#BAR GRAPH - smallmutationsindels####
small_file = '/home/ltoy/Desktop/couch/extract/graph/small_tmb_Study&Body&Tumour Mutation Burden_processed.csv'
small <- fread(small_file, header=TRUE)
s<-ggplot(small)+
    geom_bar(aes(x=fct_infreq(small$Gene), fill=small$Type)) +
    labs(title = "Small Mutations and Indels", y="Mutation Count", fill="Mutation Type") + 
    theme_classic() +
    theme(
      plot.title = element_text(hjust=0.5),
      axis.title.x=element_blank(),
      axis.title.y=element_text(size=10, vjust=2.25),
      axis.line.x=element_blank(), axis.line.y=element_blank(),
      axis.ticks.x=element_blank(),axis.ticks.y=element_blank(),
      axis.text.x=element_text(angle=90, face="italic", hjust=1, margin=margin(t=-4))
    ) + 
  facet_grid(.~Study, scales="free_x", space="free_x") #small_x.png
  #facet_grid(Study ~., scales = "free_y") #small_y.png
ggsave("/home/ltoy/Desktop/couch/extract/small_x.png", s,width=10,height=3.5)
ggsave("/home/ltoy/Desktop/couch/extract/small_y.png", s,width=9,height=10)#margin(t=-5)

#BAR GRAPH - oncosomaticCNVs####
onco_file = '/home/ltoy/Desktop/couch/extract/graph/onco_tmb_Study&Body&Tumour Mutation Burden_processed.csv'
onco <- fread(onco_file, header=TRUE)
o<-ggplot(onco)+
  geom_bar(aes(x=fct_infreq(onco$Gene), fill=onco$Alteration)) +
  labs(title = "Oncogenic Somatic CNVs", y="Mutation Count", fill="Alteration Type") + 
  theme_classic() +
  theme(
    plot.title = element_text(hjust=0.5),
    axis.title.x=element_blank(),
    axis.title.y=element_text(size=10, vjust=2.25),
    axis.line.x=element_blank(), axis.line.y=element_blank(),
    axis.ticks.x=element_blank(),axis.ticks.y=element_blank(),
    axis.text.x=element_text(angle=90, face="italic", hjust=1, margin=margin(t=-3))
  ) + 
  facet_grid(.~Study, scales="free_x", space="free_x") #onco_x.png
  #facet_grid(Study ~., scales = "free_y") #onco_y.png
ggsave("/home/ltoy/Desktop/couch/extract/onco_x.png", o, width=25,height=3.5)
ggsave("/home/ltoy/Desktop/couch/extract/onco_y.png", o, width=18,height=8) 


