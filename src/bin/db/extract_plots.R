#install packages in console by > install.packages("<name>")
#load below
library(ggplot2)
library(data.table)
library(forcats) # within tidyverse
library(cowplot)

# library(dpylr)
# library(pandas)

png("/home/ltoy/Desktop/couch/extract/small.png",width=1000,height=200)
#plot in between
dev.off()

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

#BAR GRAPH - smutind####
genemutype_file = '/home/ltoy/Desktop/couch/extract/graph/small_processed.csv'
genemutype <- fread(genemutype_file, header=TRUE)
g <-ggplot(genemutype)+
    geom_bar(aes(x=fct_infreq(genemutype$Gene), fill=genemutype$Type)) +
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
ggsave("/home/ltoy/Desktop/couch/extract/small_x.png", g, width=10,height=3.5)
ggsave("/home/ltoy/Desktop/couch/extract/small_y.png", g, width=9,height=10)#margin(t=-5)

#BAR GRAPH - oncosomaticCNVs####
genemutype_file = '/home/ltoy/Desktop/couch/extract/graph/onco_processed.csv'
genemutype <- fread(genemutype_file, header=TRUE)
g <-ggplot(genemutype)+
  geom_bar(aes(x=fct_infreq(genemutype$Gene), fill=genemutype$Alteration)) +
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
ggsave("/home/ltoy/Desktop/couch/extract/onco_x.png", g, width=25,height=3.5)
ggsave("/home/ltoy/Desktop/couch/extract/onco_y.png", g, width=18,height=8) 

#BAR GRAPH - count as label ???####
genemutype_file = '/home/ltoy/Desktop/couch/extract/oncogenicsomaticCNVs_Body_processed.csv'
genemutype <- fread(genemutype_file, header=TRUE)
#gene_freq <- as.data.frame(table(genemutype$Gene))
#sorted_freq <- gene_freq[order(-gene_freq$Freq),]
ggplot(genemutype)+
  geom_bar(aes(x=fct_infreq(genemutype$Gene),fill=genemutype$Alteration)) +
  geom_text(aes(x=fct_infreq(genemutype$Gene), y=NA, label="#"), vjust=1, angle=90, size=3)+
### how put count in as label???
  labs(title = "Oncogenic Somatic CNVs", y="Mutation Count", fill="Alteration Type") + 
  theme_classic() +
  theme(
    plot.title = element_text(hjust=0.5),
    axis.title.x=element_blank(),
    axis.title.y=element_text(size=10, vjust=2.25),
    axis.line.x=element_blank(), axis.line.y=element_blank(),
    axis.ticks.x=element_blank(),axis.ticks.y=element_blank(),
    axis.text.x=element_text(size= 5, angle=90, face="italic", hjust=0.95, margin=margin(t=-10))
  )



#ONCOPLOT ####
small_file = '/home/ltoy/Desktop/couch/extract/small_tmb_Study&Body&Tumour Mutation Burden_processed.csv'
small <- fread(small_file, header=TRUE)
onco_file = '/home/ltoy/Desktop/couch/extract/onco_tmb_Study&Body&Tumour Mutation Burden_processed.csv'
onco <- fread(onco_file, header=TRUE)
small$Field <- 'small_mutations_and_indels'
onco$Field <- 'oncogenic_somatic_CNVs'
colnames(small)[3] = "Mutation"
colnames(onco)[3] ="Mutation"
colnames(small)[1]="id"
colnames(onco)[1]="id"
combined <- rbind(small, onco)
gene_order<-data.frame(table(combined$Gene))
gene_order <- gene_order[order(-gene_order$Freq),]
cutoff = 2
subset = sum(gene_order$Freq>cutoff)
gene_subset <- gene_order[1:subset,]
gene_list = as.character(gene_subset$Var1)

header <- c("id", "Gene", "Mutation", "Study", "Field", "TMB")
newdf <- data.frame(matrix(NA, nrow=0, ncol=length(header)))
colnames(newdf) <- header
count = 0
for (row in 1:nrow(combined)){
  check_gene = as.character(combined[row, "Gene"])
  #print(check_gene)
  if(check_gene %in% gene_list){
    #print("check_gene in gene_list")
    id = as.character(combined[row, "id"])
    gene = as.character(combined[row, "Gene"])
    mutation = as.character(combined[row, "Mutation"])
    study = as.character(combined[row, "Study"])
    field = as.character(combined[row, "Field"])
    tmb = as.character(combined[row, "TMB"])
    adddf <- data.frame(matrix(NA, nrow=1, ncol=length(header)))
    colnames(adddf) <- header
    adddf[nrow(adddf) == 1] <- list(id, gene, mutation, study, field, tmb)
    newdf <- rbind(newdf, adddf)
    count = count +1
  }
}

#png("/home/ltoy/Desktop/couch/extract/onco.png",width=500,height=100)
id.num = as.numeric(as.factor(newdf$id))
gene.num = as.numeric(as.factor(fct_rev(fct_infreq(newdf$Gene))))
id.key <- levels(factor(newdf$id))
gene.key <- levels(fct_rev(fct_infreq(newdf$Gene)))
report_number = length(table(newdf$id))
onco_title = paste("Top", nrow(gene_subset), "Mutated Genes in", report_number, "Samples")
o <- 
  ggplot(newdf) +
  geom_rect(aes(xmin=id.num, xmax=id.num+1, ymin=gene.num, ymax=gene.num+1,fill=Mutation),color="white")+
  scale_x_continuous(breaks=seq(1.5, length(id.key)+0.5,1), labels=id.key, expand=c(0,0))+
  scale_y_continuous(breaks=seq(1.5, length(gene.key)+0.5,1), labels=gene.key, expand=c(0,0))+
  #labs(title = onco_title) + 
  theme(
    plot.title = element_text(size=8, hjust=0.5),
    axis.title.x=element_blank(), axis.title.y=element_blank(),
    axis.ticks.x=element_blank(),axis.ticks.y=element_blank(),
    axis.text.x=element_blank(),
    #axis.text.x=element_text(size=3, angle=90), #id
    axis.text.y=element_text(size=5, hjust=1),
    panel.grid.major = element_blank(),
    panel.grid.minor=element_line(color="white"),
    legend.position="bottom", 
    legend.title=element_blank(),
    legend.box.margin = margin(t=-10, b=0, l=-50, r=0),
    #legend.background=element_rect(color="red"),
    legend.key.size= unit(2.5, 'mm'),
    legend.text=element_text(size=5, hjust=0),
    strip.text = element_text(size=3),
  )#+
  # facet_grid(.~Study, scales="free_x", space="free_x")  #onco_x.png
#ggsave("/home/ltoy/Desktop/couch/extract/onco.png", o, width=5,height=5)
#ggsave("/home/ltoy/Desktop/couch/extract/onco_x.png", o, width=6.5,height=5) 
#ggsave("/home/ltoy/Desktop/couch/extract/onco_id.png", o, width=5,height=5) #id

oncobar_freq <- 
  ggplot(newdf)+
  geom_bar(aes(y=fct_rev(fct_infreq(Gene)), fill=Mutation))+
  labs(x="No. of Mutations")+
  theme_classic()+
  theme(
    axis.text.x = element_text(size=10),
    axis.text.y = element_blank(),
    axis.ticks.length = unit(4, "mm"),
    axis.ticks.y=element_blank(),
    axis.line.y = element_blank(),
    axis.title.x = element_text(size=10, hjust=0.5),
    axis.title.y=element_blank(),
    legend.position = "None"
  )+
  scale_x_continuous(breaks=c(0,40), limits=c(0,40), expand=c(0,0), position="top")
#ggsave("/home/ltoy/Desktop/couch/extract/onco_bar.png", oncobar_freq, width=2.5,height=5) 

id.key.df <- as.data.frame(levels(factor(newdf$id)))
id.key.df$TMB <-NA
id.key.df$Study <-NA
id.key.df$Field <-NA
colnames(id.key.df) <- c("id", "TMB", "Study", "Field")
for (id in id.key){
  extract_row <- newdf[newdf$id == id,]
  extract_tmb = as.numeric(extract_row[1,"TMB"])
  extract_study = as.character(extract_row[1,"Study"])
  extract_field = as.character(extract_row[1,"Field"])
  extract_add <- list(extract_tmb, extract_study, extract_field)
  for(row in 1:nrow(id.key.df)){
    unique_id = as.character(id.key.df[row, "id"])
    if(id == unique_id){
    id.key.df[row,] <- list(unique_id, extract_tmb, extract_study, extract_field)
    }
  }
}
oncobar_tmb <- 
ggplot(id.key.df, aes(x=id, y=TMB, fill=Study))+
  geom_bar(position='dodge', stat='identity', aes(group=Study))+
  theme_classic()+
  theme(
    legend.position = "right",
    axis.text.x = element_blank(),
    #axis.text.x = element_text(size=5, angle=90), #id
    axis.text.y=element_text(size=10),
    axis.ticks.length.y = unit(4, "mm"),
    axis.title.x=element_blank(), axis.title.y=element_text(size=15),
    axis.line.x = element_blank(), axis.ticks.x = element_blank(),
    legend.key.size = unit(8, "mm"),
    legend.title = element_blank(),
    strip.text.x=element_blank()
    )+
  scale_y_continuous(breaks=c(0,175),  limits=c(0,175), expand=c(0,0))#+
  #facet_grid(.~Study, scales="free_x", space="free_x", switch="x")  #Study
ggsave("/home/ltoy/Desktop/couch/extract/oncobar_tmb.png", oncobar_tmb, width=10,height=2.5) 

comb<-
  plot_grid(o, oncobar_freq, oncobar_tmb, nrow=1, scale=c(1,1,1)) 
ggsave("/home/ltoy/Desktop/couch/extract/comb.png", comb, width=10,height=5) 

dev.off()

#geom_tile and geom_raster ####
# ggplot(newdf) +
#   geom_raster(aes(x=id, y=fct_rev(fct_infreq(Gene)), fill=Mutation), hjust=0, vjust=0)+
#   #geom_tile(aes(x=id, y=fct_rev(fct_infreq(Gene)), fill=Mutation), color="black")+ theme()