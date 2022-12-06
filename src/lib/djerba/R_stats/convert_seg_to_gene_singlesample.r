
preProcCNA <- function(segfile, genebed, gain, amp, htz, hmz, oncolist, genelist=NA){

 # test
 #segfile="/.mounts/labs/TGL/cap/OCTCAP/OCT-01-0118/OCT-01-0118-TS/report/seg.txt"
 #genebed="/.mounts/labs/TGL/gsi/jtorchia/git/cBioWrap/files/gencode_v33_hg38_genes.bed"
 #oncolist="/.mounts/labs/TGL/gsi/jtorchia/git/cBioWrap/files/20200818-oncoKBcancerGeneList.tsv"
 #genelist="/.mounts/labs/TGL/gsi/jtorchia/git/cBioWrap/files/targeted_genelist.txt"
 #gain="0.3"
 #amp="0.7"
 #htz="-0.3"
 #hmz="-0.7"

 # read oncogenes
 oncogenes <- read.delim(oncolist, header=TRUE, row.names=1)

 ## small fix segmentation data
 segData <- read.delim(segfile, header=TRUE) # segmented data already
 segData$chrom <- gsub("chr", "", segData$chrom)

 # thresholds
 print("setting thresholds")
 gain=as.numeric(gain)
 amp=as.numeric(amp)
 htz=as.numeric(htz)
 hmz=as.numeric(hmz)

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
     df_cna_thresh[,i] <- ifelse(df_cna_thresh[,i] > amp, 2,
                         ifelse(df_cna_thresh[,i] < hmz, -2,
                             ifelse(df_cna_thresh[,i] > gain & df_cna_thresh[,i] <= amp, 1,
                                 ifelse(df_cna_thresh[,i] < htz & df_cna_thresh[,i] >= hmz, -1, 0)
                           )
                               )
                                   )
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

preProcLOH <- function(aratiofile, genebed, oncolist, genelist=NA, minCopiesForLOH=2){
  
  segments <- read.table(aratiofile,header = T)
  
  segments$chromosome <- gsub("chr", "", segments$chromosome)
  segments$ARatio <- segments$A/segments$CNt
  segments$sample <- "sample1"
  segments <- segments[segments$CNt >= minCopiesForLOH,]
  
  segments_ARatio <- segments[,c("sample","chromosome","start.pos", "end.pos","N.ratio","ARatio")]
  
  names(segments_ARatio) <- c("ID", "chrom", "loc.start" , "loc.end", "num.mark" , "seg.mean")
  
  # read oncogenes
  oncogenes <- read.delim(oncolist, header=TRUE, row.names=1)
  
  # get the gene info
  print("getting gene info for LOH")
  geneInfo <- read.delim(genebed, sep="\t", header=TRUE)
  
  cnseg_ARatio <- CNSeg(segments_ARatio)
  rdByGene_ARatio <- getRS(cnseg_ARatio, by="gene", imput=FALSE, XY=FALSE, geneMap=geneInfo, what="min")
  reducedseg_ARatio <- rs(rdByGene_ARatio)
  
  # some reformatting and return log2cna data
  df_ARatio <- subset(reducedseg_ARatio[,c(5, 6:ncol(reducedseg_ARatio))], !duplicated(reducedseg_ARatio[,c(5, 6:ncol(reducedseg_ARatio))][,1]))
  colnames(df_ARatio) <- c("Hugo_Symbol", colnames(df_ARatio)[2:ncol(df_ARatio)])
  
  # fix rownames of log2cna data
  rownames(df_ARatio) <- df_ARatio$Hugo_Symbol
  df_ARatio_onco <- df_ARatio[df_ARatio$Hugo_Symbol %in% rownames(oncogenes),]
  
  df_LOH <- df_ARatio[df_ARatio$sample1 == 0,]
  
  # subset of oncoKB genes
  df_LOH_onco <- df_LOH[df_LOH$Hugo_Symbol %in% rownames(oncogenes),]
  
  # subset if gene list given
  genelist <- unique(genelist)
  
  if (!is.na(genelist)) {
    df_ARatio <- df_ARatio[df_ARatio$Hugo_Symbol %in% genelist,]
    df_ARatio_onco <- df_ARatio_onco[df_ARatio_onco$Hugo_Symbol %in% genelist,]
    
    df_LOH <- df_LOH[df_LOH$Hugo_Symbol %in% genelist,]
    df_LOH_onco <- df_LOH_onco[df_LOH_onco$Hugo_Symbol %in% genelist,]
    
  }
  
  
  LOH=list()
  LOH[[1]] <- df_ARatio
  LOH[[2]] <- df_LOH
  LOH[[3]] <- df_ARatio_onco
  LOH[[4]] <- df_LOH_onco
  return(LOH)
  
}