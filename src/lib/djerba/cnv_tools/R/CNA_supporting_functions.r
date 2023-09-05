arm_level_caller <- function(segs, centromeres, gain_threshold, shallow_deletion_threshold, seg.perc.threshold=0.8){
  library(dplyr)
  library(data.table)
  
  #segs$seg.mean <- log(segs$depth.ratio,2)
  segs$seg.length = segs$loc.end - segs$loc.start
  
  ## roughly estimate centromere position 
  ## b/c the annotation has several centromeric regions
  centromeres.rough <- 
    centromeres %>% group_by(chrom) %>% 
    summarise(cent.start=min(chromStart),
              cent.end=max(chromEnd),
              cent.length=cent.end-cent.start,
              cent.mid=(cent.end+cent.start)/2
    )
  
  arms_n_cents <- 
    segs %>% 
    group_by(chrom) %>% 
    summarise(
      chrom.start=min(loc.start ),
      chrom.length=max(loc.end)) %>% 
    left_join(centromeres.rough,by=c("chrom"="chrom"))
  
  ## first arm is always petite (p)
  p_arms <- arms_n_cents[,c("chrom","chrom.start","cent.start")]
  names(p_arms) <- c("chrom","arm.start","arm.end")
  p_arms$arm <- "p"
  p_arms$chrom_type <- "metacentric"
  p_arms$chrom_type[p_arms$arm.start > p_arms$arm.end] <- "acrocentric"
  
  ## there should be no q-arms longer than chromosome length
  q_arms <- arms_n_cents[,c("chrom","cent.start","chrom.length")]
  names(q_arms) <- c("chrom","arm.start","arm.end")
  q_arms$arm <- "q"
  
  arm_definitions <- rbind.data.frame(
    p_arms[p_arms$chrom_type == "metacentric",-5],
    q_arms)
  arm_definitions$arm.length <- 
    arm_definitions$arm.end - arm_definitions$arm.start
  
  segs_dt <- setDT(segs) 
  arm_definitions_dt <- setDT(arm_definitions)
  
  ## join segs for being within arm boundaries
  segs_armd <- segs_dt[
    arm_definitions_dt, 
    on = .(loc.start >= arm.start, 
           loc.end <= arm.end, 
           chrom = chrom), 
    nomatch = 0,
    .(chrom,  arm, arm.length, 
       seg.mean, seg.length, loc.start, loc.end)
  ]
  
  ## use NCCN terminology
  segs_armd$CNA <- "neutral"
  segs_armd$CNA[segs_armd$seg.mean < shallow_deletion_threshold] <- "del"
  segs_armd$CNA[segs_armd$seg.mean > gain_threshold] <- "+"
  
  arm_CNA_prop <- segs_armd %>% 
    group_by(chrom,arm,CNA,arm.length) %>% 
    summarise(seg.perc=round((sum(seg.length)/mean(arm.length))*100,2)) %>%
    filter(seg.perc > seg.perc.threshold & CNA != "neutral") %>%
    arrange(-seg.perc)
  
  ## assemble annotation from columns
  arm_CNA_prop$annotation <-
    paste0(arm_CNA_prop$CNA,
           "(",
           gsub("chr","",arm_CNA_prop$chrom),
           arm_CNA_prop$arm,
           ")"
    )
  return(sort(arm_CNA_prop$annotation))
}

construct_whizbam_links <- function(df, whizbam_url) {
  if( dim(df)[[1]] == 0 ) {
  df$whizbam <- paste0(whizbam_url,
                       "&chr=", gsub("chr", "", df$Chromosome),
                       "&chrloc=", paste0(df$Start_Position, "-", df$End_Position))
  } 
  return(df)
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

