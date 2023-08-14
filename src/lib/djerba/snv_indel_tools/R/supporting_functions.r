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

construct_whizbam_links <- function(df, whizbam_url) {
  if( dim(df)[[1]] == 0 ) {
  df$whizbam <- paste0(whizbam_url,
                       "&chr=", gsub("chr", "", df$Chromosome),
                       "&chrloc=", paste0(df$Start_Position, "-", df$End_Position))
  } 
  return(df)
}

get_common_genes <- function(df, df_tcga){
  comg <- as.character(intersect(row.names(df_tcga), row.names(df)))
  df_tcga_common <- df_tcga[row.names(df_tcga) %in% comg, ]
  df_tcga_common_sort <- df_tcga_common[ order(row.names(df_tcga_common)), ]
  df_stud_common <- df[row.names(df) %in% comg, ]
  df_stud_common_sort <- df_stud_common[ order(row.names(df_stud_common)), ]
  df_stud_tcga <- merge(df_stud_common_sort, df_tcga_common_sort, by=0, all=TRUE)
  df_stud_tcga[is.na(df_stud_tcga)] <- 0
  rownames(df_stud_tcga) <- df_stud_tcga$Row.names
  df_stud_tcga$Row.names <- NULL
  return(df_stud_tcga)
}

preProcCNA <- function(segfile, genebed, cutoffs, oncolist, genelist=NA){

  # thresholds
  print("setting thresholds")
  gain = as.numeric(cutoffs["LOG_R_GAIN"] )
  amp = as.numeric(cutoffs["LOG_R_AMPL"])
  htz = as.numeric(cutoffs["LOG_R_HTZD"])
  hmz = as.numeric(cutoffs["LOG_R_HMZD"])
  
 # read oncogenes
 oncogenes <- read.delim(oncolist, header=TRUE, row.names=1)

 ## small fix segmentation data
 segData <- read.delim(segfile, header=TRUE) # segmented data already
 segData$chrom <- gsub("chr", "", segData$chrom)

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

preProcRNA <- function(gepfile, enscon, genelist = NULL){
  
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

procVEP <- function(maf_df){
  
  print("--- adding VAF column ---")
  
  # add vaf columns
  maf_df <- addVAFtoMAF(maf_df, "t_alt_count", "t_depth", "tumour_vaf")
  maf_df <- addVAFtoMAF(maf_df, "n_alt_count", "n_depth", "normal_vaf")
  
  print("--- adding oncogenic binary column ---")
  
  # add oncogenic yes or no columns
  df_anno <- transform(maf_df,
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
  
  df_filt <- subset(df_anno, TGL_FILTER_VERDICT == "PASS")
  
  return(df_filt)
}

log_r_cutoff_finder <- function(purity, MIN_LOG_ARG = 0.0078125){
  #  """Find logR cutoff values; based on legacy Perl script logRcuts.pl"""
  # MIN_LOG_ARG = 1/128 = 2^(-7)
  
  log2_with_minimum <- function(x){
    # """Return log2(x), or log2(min) if x < min; hack to avoid log(0)"""
    if (x < MIN_LOG_ARG){
      return(log2(MIN_LOG_ARG))
    }else{
      return(log2(x))
    }
  }
  
  # essentially assuming ploidy 2 (more accurately, defining htzd as loss of 0.5 ploidy and hmzd as loss of 1 ploidy)
  one_copy = purity / 2.0 
  
  # expected values for different states
  htzd = log2_with_minimum(1 - one_copy)
  hmzd = log2_with_minimum(1 - (2*one_copy))
  gain = log2_with_minimum(1 + one_copy)
  ampl = log2_with_minimum(1 + (2*one_copy))
  
  # cutoffs halfway between 0 and 1 copy, and halfway between 1 and 2 copies
  cutoffs = list(
    "LOG_R_HTZD" = htzd/2.0,
    "LOG_R_HMZD" = (hmzd-htzd)/2.0 + htzd,
    "LOG_R_GAIN" = gain/2.0,
    "LOG_R_AMPL" = (ampl-gain)/2.0 + gain
  )
  return(cutoffs)

}

