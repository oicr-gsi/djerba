#! /usr/bin/env Rscript

library(optparse)
library(data.table)
library(dplyr)

annotate_translocations <- function(fusfile, data_dir, data_file = "20240116-translocation_annotations.txt"){
  

  fus_raw = fread(fusfile)
  fus = fus_raw %>% filter(event_type %in% c("inverted translocation", "translocation") &
                             protocol == "transcriptome") %>% select(
                               
                               "break1_chromosome",
                               "break2_chromosome",
                               
                               "break1_split_reads",
                               "break2_split_reads",
                               "spanning_reads",
                               "linking_split_reads",
                               
                               "gene1_aliases",
                               "break1_position_start",
                               "break1_position_end",
                               "gene2_aliases",
                               "break2_position_start",
                               "break2_position_end",
                               "tools",
                               "call_method"
                             ) 
  
  fus$break1_chromosome[fus$break1_chromosome == "X"] <- "23"
  fus$break2_chromosome[fus$break2_chromosome == "X"] <- "23"
  
  fus$break1_chromosome <- as.numeric(fus$break1_chromosome)
  fus$break2_chromosome <- as.numeric(fus$break2_chromosome)
  
  min(fus$break1_chromosome, fus$break2_chromosome)
  
  fus <- fus %>% 
    rowwise() %>%
    mutate(min = min(break1_chromosome, break2_chromosome),
           max = max(break1_chromosome, break2_chromosome))
  
  fus$translocation <- paste0("t(",fus$min,";",fus$max,")")
  fus = fus[,!(names(fus) %in% c("min","max"))]
  fus$translocation <- gsub("23","X",x = fus$translocation)
  
  
  data_path = paste0(data_dir, "/", data_file) 
  translocation_annotations = read.table(data_path, header = T)
  
  fus_annotated <- inner_join(translocation_annotations, fus,  by=c("marker"="translocation"))
  return(fus_annotated)
}

# main function to read/write fusion data; was 'preProcFus' in Djerba classic
processFusions <- function(datafile, readfilt, entrfile){

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

 print("--- reading fusion data ---")
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

 if (nrow(data_dedup)==0) {
   print("--- Fusion data table is empty! ---")
   df_cbio <- data.frame(matrix(ncol = 10, nrow = 0))
   colnames(df_cbio) <- c("Hugo_Symbol", "Entrez_Gene_Id", "Center", "Tumor_Sample_Barcode", "Fusion", "DNA_support", "RNA_support", "Method", "Frame", "Fusion_Status")
   df_cbio_new_delim <- df_cbio
 } else {
   data_dedup$Center <- "TGL"
   data_dedup$Frame <- "frameshift"
   data_dedup$Fusion_Status <- "unknown"

   # write out the nice header
   header <- c("Hugo_Symbol", "Entrez_Gene_Id", "Center", "Tumor_Sample_Barcode", "Fusion", "DNA_support", "RNA_support", "Method", "Frame", "Fusion_Status")

   # get left gene data
   columns_left <- c("gene1_aliases", "Entrez_Gene_Id.x", "Center", "Sample", "fusion_tuples", "DNA_support", "RNA_support", "tools", "Frame", "Fusion_Status")
   data_left <- data_dedup[columns_left]
   colnames(data_left) <- header

   # get right gene data
   columns_right <- c("gene2_aliases", "Entrez_Gene_Id.y", "Center", "Sample", "fusion_tuples", "DNA_support", "RNA_support", "tools", "Frame", "Fusion_Status")
   data_right <- data_dedup[columns_right]
   colnames(data_right) <- header

   # append it all together
   df_cbio <- rbind(data_left, data_right)

   # remove rows where gene is not known (this still keeps the side of the gene which is known)
   df_cbio <- df_cbio[complete.cases(df_cbio),]
   df_cbio$Fusion <- gsub("None", "intragenic", df_cbio$Fusion)

   # change to old-style fusion delimiter for compatibiltiy with FusionAnnotator.py and OncoKB
   df_cbio_new_delim <- df_cbio
   df_cbio$Fusion <- gsub("::", "-", df_cbio$Fusion)
 }
 # input for oncoKB annotator
 df_cbio_oncokb <- df_cbio[c("Tumor_Sample_Barcode", "Fusion")]

 FUSs=list()
 FUSs[[1]] <- df_cbio
 FUSs[[2]] <- df_cbio_oncokb
 FUSs[[3]] <- df_cbio_new_delim
 return(FUSs)

}

### get parameters and call the fusion processing function ###

# get input/output paths
option_list = list(
    make_option(c("-e", "--entcon"), type="character", default=NULL, help="entrez conversion file", metavar="character"),
    make_option(c("-f", "--fusfile"), type="character", default=NULL, help="concatenated fus file", metavar="character"),
    make_option(c("-m", "--minfusionreads"), type="numeric", default=20, help="minimum read support for fusions", metavar="numeric"),
    make_option(c("-o", "--outdir"), type="character", default=NULL, help="output directory", metavar="character")
)
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE);
opt <- parse_args(opt_parser);
entcon <- opt$entcon
fusfile <- opt$fusfile
minfusionreads <- opt$minfusionreads
outdir <- opt$outdir
data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')

# check if input is empty
num_lines <- readLines(fusfile, warn=FALSE)

if(length(num_lines)<=1) {
  print("Fusion input is empty or only contains a header, processing omitted") 
} else {
  print("Processing Fusion data")

  # function returns list of 3 objects ### TO WRITE
  fusion_cbio <- processFusions(fusfile, minfusionreads, entcon)

  # write FUS files
  print("writing fus file")
  write.table(fusion_cbio[[1]], file=paste0(outdir, "/data_fusions.txt"), sep="\t", row.names=FALSE, quote=FALSE)

  # write input for oncoKB annotator
  print("writing fus file for oncokb annotator")
  write.table(fusion_cbio[[2]], file=paste0(outdir, "/data_fusions_oncokb.txt"), sep="\t", row.names=FALSE, quote=FALSE)

  # write file with new-style fusion identifiers
  print("writing fus file with new-style fusion delimiter")
  write.table(fusion_cbio[[3]], file=paste0(outdir, "/data_fusions_new_delimiter.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  
  translocations_annotated <- annotate_translocations(fusfile, data_dir)
  
  write.table(translocations_annotated,
              file=paste0(outdir, "/translocations.annotated.txt"), sep="\t", row.names=FALSE, quote=FALSE)
  
}
