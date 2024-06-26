#! /usr/bin/env Rscript

library(testthat)

basedir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), sep='/')
testdatadir <- paste(Sys.getenv(c("DJERBA_TEST_DATA")), sep='/')

source(paste0(basedir, "/plugins/wgts/cnv_purple/r/CNA_supporting_functions.r"))

test_that("arm_level_caller returns correct arm-level alterations with PURPLE input",
  {
  
    centromeres_path <- paste0(basedir,"/data/hg38_centromeres.txt")
    centromeres <- read.table(centromeres_path,header=T)
    
    gain_threshold             <- 7
    shallow_deletion_threshold <- -1
    
    segfile_path <-  paste0(testdatadir,"/plugins/cnv-purple/purple.cnv.somatic.tsv")
    segs <- read.delim(segfile_path, header=TRUE) # segmented data already
    
    expected_arm_level_calls <- sort(c("+(19p)", "+(19q)"))
    
    arm_level_calls <- arm_level_caller_purple(seg=segs, centromeres=centromeres, gain_threshold=gain_threshold, shallow_deletion_threshold=shallow_deletion_threshold, seg.perc.threshold=80)
    expect_equal(arm_level_calls, expected_arm_level_calls)
    
  }
)

test_that("preProcCNA returns correct gene-level alterations with PURPLE input", 
  {
  
    oncogenes_path <- paste0(basedir,"/data/20200818-oncoKBcancerGeneList.tsv")
    oncolist <- read.delim(oncogenes_path, header=TRUE)
    
    gene_file_path = paste0(testdatadir, "/plugins/cnv-purple/purple.cnv.gene.tsv")
    genefile <- read.delim(gene_file_path, header=TRUE) 
    ploidy=3
    
    CNAs = preProcCNA(genefile=genefile, oncolist=oncolist, ploidy=ploidy)
    df_cna_thresh_onco_nondiploid = as.data.frame(CNAs[2])
    
    expect_equal(df_cna_thresh_onco_nondiploid$minCopyNumber[df_cna_thresh_onco_nondiploid$gene == "ARID1A"], 2)
  
  }
)
  
test_that("preProcLOH returns CN and MACN info from PURPLE input for later LOH calculation", 
          {
            
            bed_path <- paste0(basedir,"/data/gencode_v33_hg38_genes.bed")
            genebed <- read.delim(bed_path, header=TRUE)
            
            segfile_path <-  paste0(testdatadir,"/plugins/cnv-purple/purple.cnv.somatic.tsv")
            segs <- read.delim(segfile_path, header=TRUE) # segmented data already
            
            segs$ID <- "purple"
            data <- segs[,c("ID","chromosome","start","end","bafCount")]
            names(data) <- c("ID",	"chrom"	,"loc.start"	,"loc.end"	,"num.mark")
            
	    # Check MACN
	    data$seg.mean <- segs$minorAlleleCopyNumber
            MACN = preProcLOH(data, genebed)
	    # filter only for TP53
            tp53 <- MACN[(which(MACN == "TP53")),]
	    expect_equal(tp53$genename, "TP53")
	    expect_equal(tp53$b_allele, 0.7342)

	    # Check CN
	    data$seg.mean <- segs$copyNumber
            CN= preProcLOH(data, genebed)
	    # filter only for TP53
            tp53 <- CN[(which(MACN == "TP53")),]
            expect_equal(tp53$genename, "TP53")
	    expect_equal(tp53$b_allele, 5.6306)

            
          }
)

