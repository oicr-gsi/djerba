#install packages in console by > install.packages("<name>")
library(ggplot2)
library(data.table)
library(forcats) # within tidyverse
library(cowplot)

#ONCOPLOT ####
small_file = '/home/ltoy/Desktop/couch/extract/small_Study&Body&Tumour Mutation Burden_processed.csv'
small <- fread(small_file, header=TRUE)
onco_file = '/home/ltoy/Desktop/couch/extract/onco_Study&Body&Tumour Mutation Burden_processed.csv'
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
cutoff = 3 ### change to make more/less Genes on y-axis - if want set number of Genes, then change code to count top n rows from top
subset = sum(gene_order$Freq>cutoff)
gene_subset <- gene_order[1:subset,]
gene_list = as.character(gene_subset$Var1)

header <- c("id", "Gene", "Mutation", "Study", "Field", "TMB")
newdf <- data.frame(matrix(NA, nrow=0, ncol=length(header)))
colnames(newdf) <- header
count = 0
for (row in 1:nrow(combined)){
  check_gene = as.character(combined[row, "Gene"])
  if(check_gene %in% gene_list){
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

id.num = as.numeric(as.factor(newdf$id))
gene.num = as.numeric(as.factor(fct_rev(fct_infreq(newdf$Gene))))
id.key <- levels(factor(newdf$id))
gene.key <- levels(fct_rev(fct_infreq(newdf$Gene)))
report_number = length(table(newdf$id))
onco_title = paste("Top", nrow(gene_subset), "Mutated Genes in", report_number, "Samples")
#for percents on right hand side of y axis
gene_subset$Percent <- NA
total_mutations = sum(gene_subset$Freq)
for (row in 1:nrow(gene_subset)){
  frequency = gene_subset[row, "Freq"]
  percent = (frequency/total_mutations * 100)
  percent = format(round(percent, 1), nsmall=1)
  percent = paste(percent,"%")
  gene_subset[row, "Percent"] <- percent
}
percent.key <- gene_subset$Percent
o <- 
  ggplot(newdf) +
  geom_rect(aes(xmin=id.num, xmax=id.num+1, ymin=gene.num, ymax=gene.num+1,fill=Mutation),color="white")+
  scale_x_continuous(breaks=seq(1.5, length(id.key)+0.5,1), labels=id.key, expand=c(0,0))+
  scale_y_continuous(breaks=seq(1.5, length(gene.key)+0.5,1), labels=gene.key, expand=c(0,0),
                     sec.axis = (sec_axis(trans=~., breaks=seq(1.5, length(gene.key)+0.5,1),labels=rev(percent.key))))+
  labs(title = onco_title) + 
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
    legend.key.size= unit(2.5, 'mm'),
    legend.text=element_text(size=5, hjust=0),
    strip.text = element_text(size=3)
  )+
  scale_fill_manual(values=c("saddlebrown","lightgoldenrod3", "forestgreen", "hotpink", "purple","cyan",
                             "gold", "royalblue", "orange", "black", "firebrick1", "chartreuse"))+
  guides(fill = guide_legend(nrow = 2))#+
 #facet_grid(.~Study, scales="free_x", space="free_x")  #onco_x.png
ggsave("/home/ltoy/Desktop/couch/extract/onco_percent.png", o, width=7,height=5)
#ggsave("/home/ltoy/Desktop/couch/extract/onco_x.png", o, width=6.5,height=5) 
#ggsave("/home/ltoy/Desktop/couch/extract/onco_id.png", o, width=5,height=5) #id

#oncobar_freq <- 
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
  scale_fill_manual(values=c("saddlebrown","lightgoldenrod3", "forestgreen", "hotpink", "purple","cyan",
                               "gold", "royalblue", "orange", "black", "firebrick1", "chartreuse"))+
  scale_x_continuous(breaks=c(0,70), limits=c(0,70), expand=c(0,0), position="top")
ggsave("/home/ltoy/Desktop/couch/extract/onco_bar.png", oncobar_freq, width=2.5,height=5) 

id.key.df <- as.data.frame(levels(factor(newdf$id)))
id.key.df$TMB <-NA
id.key.df$Study <-NA
id.key.df$Field <-NA
colnames(id.key.df) <- c("id", "TMB", "Study", "Field")
for (id in id.key){
  extract_row <- newdf[newdf$id == id,]
  extract_tmb = as.numeric(extract_row[1,"TMB"])
  if (extract_tmb > 100) { extract_tmb = 100 }
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
    legend.position = "top",
   #legend.direction = "horizontal",
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
  guides(fill = guide_legend(nrow=1))+
  scale_fill_manual(values=c("PASS01"= "deepskyblue3", "CYPRESS"="indianred2", "HPB"="goldenrod", 
                             "PANXWGTS"="cyan3",  "LBR"="chartreuse4", "VENUS"="darkorchid2"))+
  scale_y_continuous(breaks=c(0,25,50,75,100),labels=c(0,25,50,75,'>100'), limits=c(0,100), expand=c(0,0))#+
 #facet_grid(.~Study, scales="free_x", space="free_x", switch="x")  #Study
ggsave("/home/ltoy/Desktop/couch/extract/oncobar_tmb.png", oncobar_tmb, width=10,height=2.5) 

######################################################################################
#extrac onco v small percents
field_percent = as.data.frame(table(newdf$Field))
field_percent$Percent = NA
for (row in 1:nrow(field_percent)){
  value = (field_percent[row, "Freq"] / sum(field_percent$Freq) ) *100
  field_percent[row, "Percent"] = format(round(value, 1), nsmall=1)
}
ggplot(field_percent, aes(x="", y=Percent, fill=Var1))+
  geom_col()+
  coord_polar(theta="y")+
  geom_text(aes(label=paste(Var1,Percent, '%')), position=position_stack(vjust=0.5))+
  scale_fill_brewer("Blues")

#TO DO Formatting for combing 3 plots to make oncoplot in cowplot, currently align axes externally
# comb<-
#   plot_grid(o, oncobar_freq, oncobar_tmb, nrow=1, scale=c(1,1,1)) 
# ggsave("/home/ltoy/Desktop/couch/extract/comb.png", comb, width=10,height=5) 

#geom_tile and geom_raster ####
# ggplot(newdf) +
#   geom_raster(aes(x=id, y=fct_rev(fct_infreq(Gene)), fill=Mutation), hjust=0, vjust=0)+
#   #geom_tile(aes(x=id, y=fct_rev(fct_infreq(Gene)), fill=Mutation), color="black")+ theme()
