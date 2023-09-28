preProcCNA <- function(segfile, genebed, oncolist, genelist=NA){

 # read oncogenes
 oncogenes <- read.delim(oncolist, header=TRUE, row.names=1)

 ## small fix segmentation data
 segData <- read.delim(segfile, header=TRUE) # segmented data already
 segData$chrom <- gsub("chr", "", segData$chrom)

 # thresholds
 print("setting thresholds")
 amp=as.numeric(4)


 # get the gene info
 print("getting gene info")
 geneInfo <- read.delim(genebed, sep="\t", header=TRUE)

 # make CN matrix gene level
 print("converting seg")
 cnseg <- CNSeg(segData)
 rdByGene <- getRS(cnseg, by="gene", imput=FALSE, XY=FALSE, geneMap=geneInfo, what="min")
 reducedseg <- rs(rdByGene)

 # some reformatting and return log2cna data
 df_cna <- subset(reducedseg[,c(5, 6:ncol(reducedseg))], !duplicated(reducedseg[,c(5, 6:ncol(reducedseg))][,1]))
 colnames(df_cna) <- c("Hugo_Symbol", colnames(df_cna)[2:ncol(df_cna)])

 # set thresholds and return 5-state matrix
 print("thresholding cnas")
 df_cna_thresh <- df_cna
 df_cna_thresh[,c(2:ncol(df_cna))] <- sapply(df_cna_thresh[,c(2:ncol(df_cna))], as.numeric)
 # threshold data
 for (i in 2:ncol(df_cna_thresh))
 {
     df_cna_thresh[,i] <- ifelse(df_cna_thresh[,i] >= amp, 2, 0)
 }

 # fix rownames of log2cna data
 rownames(df_cna) <- df_cna$Hugo_Symbol
 df_cna$Hugo_Symbol <- NULL
 df_cna <- signif(df_cna, digits=4)

 # fix rownames of thresholded data
 row.names(df_cna_thresh) <- df_cna_thresh[,1]
  
 # subset of oncoKB genes
 df_cna_thresh_onco <- df_cna_thresh[df_cna_thresh$Hugo_Symbol %in% rownames(oncogenes),]

 # subset of oncoKB genes with non-diploid genes
 df_cna_thresh_onco_nondiploid <- df_cna_thresh_onco[(df_cna_thresh_onco[,2] != 0), ]

 # subset if gene list given
 if (!is.na(genelist)) {
    keep_genes <- readLines(genelist)
    df_cna$Hugo_Symbol <- row.names(df_cna)
    df_cna <- df_cna[df_cna$Hugo_Symbol %in% keep_genes,]
    df_cna_thresh <- df_cna_thresh[df_cna_thresh$Hugo_Symbol %in% keep_genes,]
 }

 # remove Hugo
 df_cna$Hugo_Symbol <- NULL
 df_cna_thresh$Hugo_Symbol <- NULL
 df_cna_thresh_onco$Hugo_Symbol <- NULL
 df_cna_thresh_onco_nondiploid$Hugo_Symbol <- NULL

 # return the list of dfs
 CNAs=list()
 CNAs[[1]] <- segData
 CNAs[[2]] <- df_cna
 CNAs[[3]] <- df_cna_thresh
 CNAs[[4]] <- df_cna_thresh_onco
 CNAs[[5]] <- df_cna_thresh_onco_nondiploid
 return(CNAs)

}
