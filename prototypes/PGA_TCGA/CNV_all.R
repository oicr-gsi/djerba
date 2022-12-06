library(tidyverse)
library(data.table)
library(jsonlite)

#process metadata
raw_json <- jsonlite::read_json('metadata.cart.2022-09-20.json')

sample_info <- data.frame("entity_id1"=NA,"entity_id2"=NA,"case_id"=NA)

for(i in c(1:length(raw_json))){
  sample_info[nrow(sample_info) + 1,] <- 
    c(raw_json[[i]]$associated_entities[[1]]$entity_id,
      raw_json[[i]]$associated_entities[[2]]$entity_id,
      raw_json[[i]]$associated_entities[[1]]$case_id)
}

PGAs <- read.table('PGA.all.txt')[,-1]
names(PGAs) <- c('sample','PGA')

#process PGA data
PGA_sample <- left_join(PGAs,sample_info,by=c('sample'='entity_id1')) %>% left_join(sample_info,by=c('sample'='entity_id2'))
PGA_sample$case_id.x[is.na(PGA_sample$case_id.x)] <- PGA_sample$case_id.y[is.na(PGA_sample$case_id.x)]
PGA_sample_short <- PGA_sample %>% dplyr::select(sample,case_id.x,PGA) %>% distinct(sample,case_id.x,PGA, .keep_all = TRUE)

#process clinical data

clinical <- fread('clinical.cart.2022-09-20/clinical.tsv')
clinical_short <- clinical %>% dplyr::select(case_id,classification_of_tumor,primary_diagnosis,site_of_resection_or_biopsy,tissue_or_organ_of_origin,metastasis_at_diagnosis_site)
clinical_PGA <- left_join(PGA_sample_short,clinical_short,by=c("case_id.x"="case_id"))
clinical_PGA <- clinical_PGA[!duplicated(clinical_PGA),]

clinical_PGA[clinical_PGA == "'--"] <- NA
clinical_PGA[clinical_PGA == "not reported"] <- NA
clinical_PGA[clinical_PGA == "Not Reported"] <- NA
clinical_PGA[clinical_PGA == "Not Unknown"] <- NA

write.table(clinical_PGA,file = "pgacomp-tcga.txt",quote = FALSE,row.names = FALSE,sep = "\t")

