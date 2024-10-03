#! /usr/bin/env Rscript

library(optparse)
library(data.table)
library(dplyr)

'%ni%' <- function(x,y)!('%in%'(x,y))


# main function to read/write fusion data; was 'preProcFus' in Djerba classic
processFusions <- function(datafile, readfilt, entrfile, arribafile ){
  
 # function to split and take max value from list of columns
 split_column_take_max <- function(df, columns) {
  for (column in columns) {
   splitup <- as.data.frame(do.call(rbind, strsplit(as.character(df[[column]]), ';')), stringsAsFactors=FALSE)
   splitup[splitup=="None"] <- 0
   splitup[1:ncol(splitup)] <- sapply(splitup[1:ncol(splitup)], as.numeric)
   bspot<-which(names(df)==column)
   df[[column]] <- apply(splitup, 1, max)
  }
   return(df)
 }

 cat("reading fusion data...\n")
 data <- read.csv(datafile, sep="\t", header=TRUE, check.names=FALSE, stringsAsFactors=FALSE)
 entr <- read.csv(entrfile, sep="\t", header=TRUE, check.names=FALSE, stringsAsFactors=FALSE)

 # reformat the filtering columns to split and take the max value within cell
 columns <- c("contig_remapped_reads", "flanking_pairs", "break1_split_reads", "break2_split_reads", "linking_split_reads")
 data <- split_column_take_max(data, columns)

 # add a column which pulls the correct read support columns
 data$read_support <- ifelse(data$call_method == "contig", data$contig_remapped_reads,
                        ifelse(data$call_method == "flanking reads", data$flanking_pairs,
                             ifelse(data$call_method == "split reads", data$break1_split_reads + data$break2_split_reads + data$linking_split_reads, 0)
                           )
                               )

 # filter by minimum read support
 data <- data[data$read_support > readfilt, ]

 # sort descending read support
 data <- data[order(-data$read_support), ]

 # get unique fusions for each sample
 # :: is the new-style fusion delimiter, see https://www.nature.com/articles/s41375-021-01436-6
 data$fusion_tuples <- apply(data[, c("gene1_aliases", "gene2_aliases")], 1, function(x) paste0(sort(x), collapse = "::"))

 # add index which is sample, tuple
 data$index <- paste0(data$Sample, data$fusion_tuples)


 # deduplicate
 data_dedup <- data[!duplicated(data$index),]

 # gene1 should not equal gene2
 data_dedup <- data_dedup[data_dedup$gene1_aliases != data_dedup$gene2_aliases, ]

 # merge in entrez gene ids
 data_dedup <- merge(data_dedup, entr, by.x="gene1_aliases", by.y="Hugo_Symbol", all.x=TRUE)
 data_dedup <- merge(data_dedup, entr, by.x="gene2_aliases", by.y="Hugo_Symbol", all.x=TRUE)



 # add some missing columns
 data_dedup$DNA_support <- ifelse(grepl("delly", data_dedup$tools), "yes", "no")
 data_dedup$RNA_support <- ifelse(grepl("arriba", data_dedup$tools), "yes", 
                              ifelse(grepl("star", data_dedup$tools), "yes", "no")
                                )

 #### add translocation style ####
 
 
 data_dedup$break1_chromosome_num <- data_dedup$break1_chromosome
 data_dedup$break2_chromosome_num <- data_dedup$break2_chromosome
 
 data_dedup$break1_chromosome_num[data_dedup$break1_chromosome_num == "X"] <- "23"
 data_dedup$break2_chromosome_num[data_dedup$break2_chromosome_num == "X"] <- "23"
 
 data_dedup$break1_chromosome_num <- as.numeric(data_dedup$break1_chromosome_num)
 data_dedup$break2_chromosome_num <- as.numeric(data_dedup$break2_chromosome_num)
 
 data_dedup <- data_dedup %>% 
   rowwise() %>%
   mutate(min = min(break1_chromosome_num, break2_chromosome_num),
          max = max(break1_chromosome_num, break2_chromosome_num))
 
 data_dedup$translocation <- paste0("t(",data_dedup$min,";",data_dedup$max,")")


 data_dedup = data_dedup[,!(names(data_dedup) %in% c("min","max"))]
 data_dedup$translocation <- gsub("23","X",x = data_dedup$translocation)
 
 data_dedup$translocation[data_dedup$event_type %ni% c("inverted translocation", "translocation")] <- data_dedup$event_type[data_dedup$event_type %ni% c("inverted translocation", "translocation")]
 
 data_dedup$translocation[data_dedup$event_type == "inversion"] <- paste0("inv(",data_dedup$break1_chromosome[data_dedup$event_type == "inversion"],")")

 #####
 cat("Adding Arriba data...\n")
 
 arriba <- read.csv(arribafile, sep="\t", header=TRUE, check.names=FALSE, stringsAsFactors=FALSE)
 arriba$arriba <- "arriba"
 if(length(arriba$reading_frame[arriba$reading_frame == "."]) > 0){
   cat("Replacing . reading frame with Unknown\n")
  arriba$reading_frame[arriba$reading_frame == "."] <- "Unknown"
 }
 names(arriba)[1] <- "gene1"
 
 intersecting_genes <- intersect(unique(c(arriba$gene2,arriba$gene1)),unique(c(data_dedup$gene1_aliases,data_dedup$gene2_aliases)))
 arriba$gene1[arriba$gene1 %ni% intersecting_genes ] <- "None"
 arriba$gene2[arriba$gene2 %ni% intersecting_genes ] <- "None"
 
 arriba <- arriba %>%
   rowwise() %>%      # for each row
   mutate(fusion_alpha = paste(sort(c(gene1, gene2)), collapse = " - ")) %>%  # sort alphabetically and then combine them separating with -
   ungroup() 
 
 data_dedup <- data_dedup %>%
   rowwise() %>%      # for each row
   mutate(fusion_alpha = paste(sort(c(gene1_aliases, gene2_aliases)), collapse = " - ")) %>%  # sort alphabetically and then combine them separating with -
   ungroup() 
 

 data_dedup <- left_join(data_dedup, arriba, by=c("fusion_alpha"="fusion_alpha"))
 
 if(length(data_dedup$reading_frame[is.na(data_dedup$reading_frame)]) > 0){
    cat("Replacing empty reading frame with Undertermined\n")
    data_dedup$reading_frame[is.na(data_dedup$reading_frame)] <- "Undetermined"
 }
 
 #### split into tables ####
 
 header <- c("Hugo_Symbol", "Entrez_Gene_Id",  "Tumor_Sample_Barcode", "Fusion", "DNA_support", "RNA_support", "Method", "translocation", "arriba_site1", "arriba_site2", "Frame")
 
 if (nrow(data_dedup)==0) {
   
   print("--- Fusion data table is empty! ---")

   df_cbio <- data.frame(matrix(ncol = length(header), nrow = 0))
   colnames(df_cbio) <- header
   df_cbio_new_delim <- df_cbio
   
 } else {

   # get left gene data
   columns_left <- c("gene1_aliases", "Entrez_Gene_Id.x",  "Sample", "fusion_tuples", "DNA_support", "RNA_support", "tools", "translocation", "site1", "site2", "reading_frame")
   data_left <- data_dedup[columns_left]
   colnames(data_left) <- header

   # get right gene data
   columns_right <- c("gene2_aliases", "Entrez_Gene_Id.y", "Sample", "fusion_tuples", "DNA_support", "RNA_support", "tools", "translocation", "site1", "site2", "reading_frame")
   data_right <- data_dedup[columns_right]
   colnames(data_right) <- header

   # append it all together
   df_cbio <- rbind(data_left, data_right)

   # remove rows where gene is not known (this still keeps the side of the gene which is known)
   df_cbio <- df_cbio[!is.na(df_cbio$Entrez_Gene_Id),]
   df_cbio$Fusion <- gsub("None", "intragenic", df_cbio$Fusion)

   # change to old-style fusion delimiter for compatability with OncoKB's FusionAnnotator.py 
   df_cbio$Fusion_newStyle <- df_cbio$Fusion
   df_cbio$Fusion <- gsub("::", "-", df_cbio$Fusion)
   
   df_cbio <- df_cbio[!duplicated(df_cbio),]
   
   # deal with cases where there is more than one possible reading frame
   multiple_frames <- names(table(df_cbio$Fusion)[table(df_cbio$Fusion) > 2 ])
   df_cbio$Frame[df_cbio$Fusion %in% multiple_frames] <- "Multiple Frames"
   df_cbio$arriba_site1[df_cbio$Fusion %in% multiple_frames] <- "Multiple Sites"
   df_cbio$arriba_site2[df_cbio$Fusion %in% multiple_frames] <- "Multiple Sites"
   
   df_cbio <- df_cbio[!duplicated(df_cbio),]
   
 }
 
 # input for oncoKB annotator
 df_cbio_oncokb <- df_cbio[c("Tumor_Sample_Barcode", "Fusion")]

 FUSs=list()
 FUSs[[1]] <- df_cbio
 FUSs[[2]] <- df_cbio_oncokb
 return(FUSs)

}

### get parameters and call the fusion processing function ###

# get input/output paths
option_list = list(
    make_option(c("-e", "--entcon"), type="character", default=NULL, help="entrez conversion file", metavar="character"),
    make_option(c("-f", "--fusfile"), type="character", default=NULL, help="concatenated fus file", metavar="character"),
    make_option(c("-A", "--arriba"), type="character", default=NULL, help="arriba file", metavar="character"),
    make_option(c("-m", "--minfusionreads"), type="numeric", default=20, help="minimum read support for fusions", metavar="numeric"),
    make_option(c("-w", "--workdir"), type="character", default=NULL, help="output directory", metavar="character"),
    make_option(c("-o", "--oncotree"), type="character", default=NULL, help="oncotree code", metavar="character"),
    make_option(c("-a", "--annotation_file"), type="character", default="NCCN_annotations.txt", help="translocation_annotations", metavar="character")
)

opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE);
opt <- parse_args(opt_parser);
entcon <- opt$entcon
fusfile <- opt$fusfile
arribafile <- opt$arriba
minfusionreads <- opt$minfusionreads
outdir <- opt$workdir
annotation_file <- opt$annotation_file
oncotree <- opt$oncotree
data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')

# check if input is empty
num_lines <- readLines(fusfile, warn=FALSE)

if(length(num_lines)<=1) {
  print("Fusion input is empty or only contains a header, processing omitted") 
} else {
  print("Processing Fusion data")

  # function returns list of 3 objects ### TO WRITE
  fusion_cbio <- processFusions(fusfile, minfusionreads, entcon, arribafile)
  # write input for oncoKB annotator
  print("writing fus file for oncokb annotator")
  write.table(fusion_cbio[[1]], file=paste0(outdir, "/data_fusions.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  
  # write input for oncoKB annotator
  print("writing fus file for oncokb annotator")
  write.table(fusion_cbio[[2]], file=paste0(outdir, "/data_fusions_oncokb.txt"), sep="\t", row.names=FALSE, quote=FALSE)

  annotation_path = paste0(data_dir, "/", annotation_file) 
  translocation_annotations = read.table(annotation_path, header = T)


  # Fix potential NA or empty values in translocation column
  fusion_cbio[[1]]$translocation[is.na(fusion_cbio[[1]]$translocation) | fusion_cbio[[1]]$translocation == ""] <- "Unknown"
  
  # Data type match before the join
  fusion_cbio[[1]]$translocation <- as.character(fusion_cbio[[1]]$translocation)
  translocation_annotations$marker <- as.character(translocation_annotations$marker)

  # Perform the join
  fus_annotated <- inner_join(translocation_annotations, fusion_cbio[[1]], by = c("marker" = "translocation"))

  fus_annotated <- fus_annotated[fus_annotated$oncotree == oncotree,]
  fus_annotated <- fus_annotated[c("Tumor_Sample_Barcode", "Fusion")]
  write.table(fus_annotated, file=paste0(outdir, "/data_fusions_NCCN.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  
}
