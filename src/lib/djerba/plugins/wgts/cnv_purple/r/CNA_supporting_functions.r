arm_level_caller_purple <- function(segs, centromeres, gain_threshold, shallow_deletion_threshold, seg.perc.threshold=80, baf.min=50){
  #' Take segment information and turn into chromosome arm level AMP/DEL calls, assuming $seg.perc.threshold is AMP'd or DEL'd
  
  library(dplyr)
  library(data.table)
  
  segs$seg.length = segs$end - segs$start
  
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
    group_by(chromosome) %>% 
    summarise(
      chrom.start=min(start),
      chrom.length=max(end)) %>% 
    left_join(centromeres.rough,by=c("chromosome"="chrom"))
  
  ## first arm is always petite (p)
  p_arms <- arms_n_cents[,c("chromosome","chrom.start","cent.start")]
  names(p_arms) <- c("chrom","arm.start","arm.end")
  p_arms$arm <- "p"
  p_arms$chrom_type <- "metacentric"
  p_arms$chrom_type[p_arms$arm.start > p_arms$arm.end] <- "acrocentric"
  
  ## there should be no q-arms longer than chromosome length
  q_arms <- arms_n_cents[,c("chromosome","cent.start","chrom.length")]
  names(q_arms) <- c("chrom","arm.start","arm.end")
  q_arms$arm <- "q"
  
  arm_definitions <- rbind.data.frame(
    p_arms[p_arms$chrom_type == "metacentric",-5],
    q_arms)
  arm_definitions$arm.length <- 
    arm_definitions$arm.end - arm_definitions$arm.start
  
  segs_dt <- setDT(segs[,c("chromosome","start","end","copyNumber","seg.length")]) 
  arm_definitions_dt <- setDT(arm_definitions)
  
  ## join segs for being within arm boundaries
  segs_armd <- segs_dt[
    arm_definitions_dt, 
    on = .(start >= arm.start, 
           end <= arm.end, 
           chromosome = chrom), 
    nomatch = 0,
    .(chrom,  arm, arm.length, 
      copyNumber, seg.length, start, end)
  ]
  
  ## use NCCN terminology
  segs_armd$CNA <- "neutral"
  segs_armd$CNA[segs_armd$copyNumber < shallow_deletion_threshold] <- "del"
  segs_armd$CNA[segs_armd$copyNumber > gain_threshold] <- "+"
  
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


construct_whizbam_links <- function(segs, whizbam_url) {
  if( dim(segs)[[1]] > 0 ) {
    segs$whizbam <- paste0(whizbam_url,
                           "&chr=", gsub("chr", "", segs$chromosome),
                           "&chrloc=", paste0(segs$start, "-", segs$end))
  } 
  return(segs)
}

preProcCNA <- function(genefile, oncolist, tumour_id, ploidy=2, ploidy_multiplier=2.4){
  #' take segment-level CNV calls and translate to genes
  
  amp = ploidy_multiplier * ploidy
  hmz = 0.5
  
  oncogenes <- oncolist$Hugo.Symbol[oncolist$OncoKB.Annotated == "Yes"]
  
  df_cna_thresh <-  genefile[,c("gene","minCopyNumber")]
 
  # "minCopyNumber" should actually be the tumour ID instead. 
  # Rename the column to be tumour ID.
  names(df_cna_thresh)[2] <- tumour_id

  # threshold data
  for (i in 2:ncol(df_cna_thresh))
  {
     df_cna_thresh[,i] <- ifelse(df_cna_thresh[,i] > amp, 2,
                            ifelse(df_cna_thresh[,i] < hmz, -2, 0)
                          )
                                   
  }
  
 # fix rownames of thresholded data
 row.names(df_cna_thresh) <- df_cna_thresh[,1]
 
 # subset of oncoKB genes
 df_cna_thresh_onco <- df_cna_thresh[df_cna_thresh$gene %in% oncogenes,]

 # subset of oncoKB genes with non-diploid genes
 df_cna_thresh_onco_nondiploid <- df_cna_thresh_onco[(df_cna_thresh_onco[,2] != 0), ]

 df_cna_thresh$Hugo_Symbol <- NULL
 df_cna_thresh_onco_nondiploid$gene <- NULL
 
 # return the list of dfs
 CNAs=list()
 CNAs[[1]] <- df_cna_thresh
 CNAs[[2]] <- df_cna_thresh_onco_nondiploid
 return(CNAs)

}


preProcLOH <- function(segments, genebed){
  library(CNTools)
  
  segments$chrom <- gsub("chr", "", segments$chrom)
  segments$ID <- "b_allele"
  
  cnseg_ARatio <- CNSeg(segments)
  rdByGene_ARatio <- getRS(cnseg_ARatio, by="gene", imput=FALSE, XY=FALSE, geneMap=genebed, what="min")
  reducedseg_ARatio <- rs(rdByGene_ARatio)
  
  a_allele <- reducedseg_ARatio[,c("genename","b_allele")]

  return(a_allele)
  
}

process_centromeres <- function(centromeres_path){
  #' Add some columns to the centromere file so it plots pretty in CNV track
  centromeres <- read.table(centromeres_path,header=T)
  centromeres <- separate(centromeres,chrom,c("blank","chr"),"chr",fill="left",remove = FALSE)
  centromeres$Chr <- factor(c(centromeres$chr), levels = c(1:22,"X"))
  centromeres <- centromeres %>% filter(!is.na(Chr))
  
  centromeres_sub <- centromeres %>% dplyr::select(chromStart,chromEnd,Chr)
  names(centromeres_sub) <- c("start","end","Chromosome")
  centromeres_sub$majorAlleleCopyNumber <- NA
  centromeres_sub$minorAlleleCopyNumber <- NA
  centromeres_sub$CNt_high <- NA
  centromeres_sub$copyNumber <- NA
  centromeres_sub$cent <- 1
  return(centromeres_sub)
}
