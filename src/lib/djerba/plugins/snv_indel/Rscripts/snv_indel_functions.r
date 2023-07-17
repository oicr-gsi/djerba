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

addVAFtoMAF <- function(maf_df, alt_col, dep_col, vaf_header) {

 # print a warning if any values are missing (shouldn't happen), but change them to 0
 if(anyNA(maf_df[[alt_col]]) || anyNA(maf_df[[dep_col]])) {
    print("Warning! Missing values found in one of the count columns")
    maf_df[[alt_col]][is.na(maf_df[[alt_col]])] <- 0
    maf_df[[dep_col]][is.na(maf_df[[dep_col]])] <- 0
 }

 # ensure factors end up as numeric
 maf_df[[alt_col]] <- as.numeric(as.character(maf_df[[alt_col]]))
 maf_df[[dep_col]] <- as.numeric(as.character(maf_df[[dep_col]]))

 # ensure position comes after alternate count field
 bspot                  <- which(names(maf_df)==alt_col)
 maf_df                 <- data.frame(maf_df[1:bspot], vaf_temp=maf_df[[alt_col]]/maf_df[[dep_col]], maf_df[(bspot+1):ncol(maf_df)], check.names=FALSE)
 names(maf_df)[bspot+1] <- vaf_header

 # check for any NAs
 if(anyNA(maf_df[[vaf_header]])) {
    print("Warning! There are missing values in the new vaf column")
    maf_df[[vaf_header]][is.na(maf_df[[vaf_header]])] <- 0
 }

 return(maf_df)
}
procVEP <- function(datafile){

 #datafile <- "T:/gsi/jtorchia/cap/PASS01/PANX_1213/PANX_1213_Pm_M_100-009-01_876211_FzTB_4_FzTS_2_LCM_1/1.0/report/maf.txt"

 print("--- reading data ---")
 data <- read.csv(datafile, sep="\t", header=TRUE, check.names=FALSE, stringsAsFactors=FALSE)

 print("--- adding VAF column ---")

 # add vaf columns
 data <- addVAFtoMAF(data, "t_alt_count", "t_depth", "tumour_vaf")
 data <- addVAFtoMAF(data, "n_alt_count", "n_depth", "normal_vaf")

 # clear memory (important when the mafs are huge - will maybe outgrow R if files are millions and millions of lines)
 df_anno <- data
 gc()

 print("--- adding oncogenic binary column ---")

 # add oncogenic yes or no columns
 df_anno <- transform(df_anno,
    oncogenic_binary = ifelse(ONCOGENIC == "Oncogenic" | ONCOGENIC == "Likely Oncogenic",
                        "YES", "NO")
 )

 print("--- adding common_variant binary column ---")

 # add common_variant yes or no columns
 df_anno <- transform(df_anno,
    ExAC_common = ifelse(grepl("common_variant", df_anno$FILTER),
                        "YES", "NO")
 )

 print("--- adding gnomAD_AF_POPMAX binary column ---")

 # add POPMAX yes or no columns
 gnomad_cols <- c("gnomAD_AFR_AF", "gnomAD_AMR_AF", "gnomAD_ASJ_AF", "gnomAD_EAS_AF", "gnomAD_FIN_AF", "gnomAD_NFE_AF", "gnomAD_OTH_AF", "gnomAD_SAS_AF")
 df_anno[gnomad_cols][is.na(df_anno[gnomad_cols])] <- 0
 df_anno[, "gnomAD_AF_POPMAX"] <- apply(df_anno[gnomad_cols], 1, max)

 print("--- small change to filters ---")
 # caller artifact filters
 df_anno$FILTER <- gsub("^clustered_events$",
                        "PASS",
                        df_anno$FILTER)

 df_anno$FILTER <- gsub("^clustered_events;common_variant$",
                        "PASS",
                        df_anno$FILTER)

 df_anno$FILTER <- gsub("^common_variant$",
                        "PASS",
                        df_anno$FILTER)

 df_anno$FILTER <- gsub(".",
                        "PASS",
                        df_anno$FILTER,
                        fixed=TRUE)

 # Artifact Filter
 print("--- artifact filter ---")
 df_anno <- transform(df_anno,
  TGL_FILTER_ARTIFACT = ifelse(FILTER == "PASS",
                      "PASS", "Artifact")
 )

 # ExAC Filter
 print("--- exac filter ---")
 df_anno <- transform(df_anno,
  TGL_FILTER_ExAC = ifelse(ExAC_common == "YES" & Matched_Norm_Sample_Barcode == "unmatched",
                      "ExAC_common", "PASS")
 )

 # gnomAD_AF_POPMAX Filter
 print("--- gnomAD filter ---")
 df_anno <- transform(df_anno,
  TGL_FILTER_gnomAD = ifelse(gnomAD_AF_POPMAX > 0.001 & Matched_Norm_Sample_Barcode == "unmatched",
                      "gnomAD_common", "PASS")
 )

 # VAF Filter
 print("--- VAF filter ---")
 df_anno <- transform(df_anno,
  TGL_FILTER_VAF = ifelse(tumour_vaf >= 0.15 | (tumour_vaf < 0.15 & oncogenic_binary == "YES"),
                      "PASS", "low_VAF")
 )

 # Mark filters
 print("--- printing verdict ---")
 df_anno <- transform(df_anno,
  TGL_FILTER_VERDICT = ifelse(TGL_FILTER_ARTIFACT == "PASS" & TGL_FILTER_ExAC == "PASS" & TGL_FILTER_gnomAD == "PASS" & TGL_FILTER_VAF == "PASS",
                      "PASS",
                       paste(df_anno$TGL_FILTER_ARTIFACT, df_anno$TGL_FILTER_ExAC, TGL_FILTER_gnomAD, df_anno$TGL_FILTER_VAF, sep=";"))
 )

 return(df_anno)
 }

construct_whizbam_links <- function(df, whizbam_url, studyid, tumourid, normalid, seqtype, genome) {
   #whizbam_url <- "whizbam.oicr.on.ca"
   #studyid <- "OCTCAP"
   #tumourid <- "OCT_011408-TS"
   #normalid <- "OCT-01-1408-BC-10"
   #seqtype <- "GENOME"
   #genome <- "hg38"
   df$whizbam <- paste0(whizbam_url,
                        "/igv?project1=", studyid,
                        "&library1=", tumourid,
                        "&file1=", tumourid, ".bam",
                        "&seqtype1=", seqtype,
                        "&project2=", studyid,
                        "&library2=", normalid,
                        "&file2=", normalid, ".bam",
                        "&seqtype2=", seqtype,
                        "&chr=", gsub("chr", "", df$Chromosome),
                        "&chrloc=", paste0(df$Start_Position, "-", df$End_Position),
                        "&genome=", genome)

   df_whizbam <- df
   return(df_whizbam)

}

# preprocess function
preProcRNA <- function(gepfile, enscon, genelist = NULL){

 # testing:
 #gepfile="T:/gsi/jtorchia/pipeline/data/OCTCAP/cbioportal/cBioWrap_20200204/output/gepdir/input.fpkm.txt"
 #enscon="T:/gsi/jtorchia/git/cBioWrap/files/ensemble_conversion.txt"
 #genelist="T:/gsi/jtorchia/git/cBioWrap/files/targeted_genelist.txt"

 # read in data
 gepData <- read.csv(gepfile, sep="\t", header=TRUE, check.names=FALSE)
 ensConv <- read.csv(enscon, sep="\t", header=FALSE)

 # rename columns
 colnames(ensConv) <- c("gene_id", "Hugo_Symbol")

 # merge in Hugo's, re-order columns, deduplicate
 df <- merge(x=gepData, y=ensConv, by="gene_id", all.x=TRUE)
 df <- subset(df[,c(ncol(df),2:(ncol(df)-1))], !duplicated(df[,c(ncol(df),2:(ncol(df)-1))][,1]))
 df <- df[!is.na(df$Hugo_Symbol),]
 row.names(df) <- df[,1]
 df <- df[,-1]

 # subset if gene list given
 if (!is.null(genelist)) {
	keep_genes <- readLines(genelist)
	df <- df[row.names(df) %in% keep_genes,]
 }

 # return the data frame
 return(df)
}

# simple zscore function
compZ <- function(df) {

 # scale row-wise
 df_zscore <- t(scale(t(df)))

 # NaN (when SD is 0) becomes 0
 df_zscore[is.nan(df_zscore)] <- 0

 # we want a dataframe
 df_zscore <- data.frame(signif(df_zscore, digits=4), check.names=FALSE)

 return(df_zscore)
}


plot_dcSigs <- function(df_snv, plotdir) {

   # fix formatting
   df_snv$Tumor_Sample_Barcode <- as.character(df_snv$Tumor_Sample_Barcode)

   # read input data
   sigs_input <- mut.to.sigs.input(mut.ref=df_snv,
                                sample.id="Tumor_Sample_Barcode",
                                chr="Chromosome",
                                pos="Start_Position",
                                ref="Reference_Allele",
                                alt="Allele",
                                bsg=BSgenome.Hsapiens.UCSC.hg38)

   # calculate a sample
   samplelist <- as.character(unique(df_snv$Tumor_Sample_Barcode))
   df_weights <- NULL
   for (sample in samplelist)
    {
       sample_sigs <- whichSignatures(tumor.ref=sigs_input,
                           signatures.ref=signatures.nature2013,
                           sample.id=sample,
                           contexts.needed=TRUE,
                           tri.counts.method='exome')

       # plot the normed value
       #png(file=paste(plotdir, "/", sample,".dcSigs_norm.png", sep=""), units="px", height=700, width=1000)
        #print({
        #    plotSignatures(sample_sigs, sub=sample)
        #})
       #dev.off()

       # get signature weights
       weights <- sample_sigs$weights
       df_weights <- rbind(df_weights, weights)
    }

return(df_weights)

}
