#! /usr/bin/env Rscript

library(testthat)

basedir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), sep='/')
testdatadir <- paste(Sys.getenv(c("DJERBA_TEST_DATA")), sep='/')

source(paste0(basedir, "/plugins/wgts/cnv_purple/CNA_supporting_functions.r"))

test_that("arm_level_caller returns correct arm-level alterations with Sequenza input",
  {
  
    centromeres_path <- paste0(basedir,"/data/hg38_centromeres.txt")
    centromeres <- read.table(centromeres_path,header=T)
    
    gain_threshold             <- 0.6
    shallow_deletion_threshold <- -0.6
    
    sequenza_segfile_path <-  paste0(testdatadir,"/report_example/data_segments.txt")
    segs <- read.delim(sequenza_segfile_path, header=TRUE) # segmented data already
    segs$chrom <- paste0("chr",segs$chrom)
    
    expected_arm_level_calls <- sort(c("+(12p)","+(3q)","del(22p)"))
    
    arm_level_calls <- arm_level_caller(seg=segs, centromeres=centromeres, gain_threshold=gain_threshold, shallow_deletion_threshold=shallow_deletion_threshold, seg.perc.threshold=0.5)
    expect_equal(arm_level_calls, expected_arm_level_calls)
    
  }
)

test_that("preProcCNA returns correct gene-level alterations with PURPLE input", 
  {
  
    oncogenes_path <- paste0(basedir,"/data/20200818-oncoKBcancerGeneList.tsv")
    oncolist <- read.delim(oncogenes_path, header=TRUE)
    
    gene_file_path = paste0(testdatadir, "/wgs-cnv-plugin/OCT_011657_Co_P_OCT_011657-TS.purple/OCT_011657_Co_P_OCT_011657-TS.purple.cnv.gene.tsv")
    genefile <- read.delim(gene_file_path, header=TRUE) 
    ploidy=3
    
    CNAs = preProcCNA(genefile=genefile, oncolist=oncolist, ploidy=ploidy)
    df_cna_thresh_onco_nondiploid = as.data.frame(CNAs[2])
    
    expect_equal(df_cna_thresh_onco_nondiploid$minCopyNumber[df_cna_thresh_onco_nondiploid$gene == "ARID1A"], 2)
  
  }
)
  

