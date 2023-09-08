#! /usr/bin/env Rscript

library(testthat)

basedir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), sep='/')
testdatadir <- paste(Sys.getenv(c("DJERBA_TEST_DATA")), sep='/')

source(paste0(basedir, "/plugins/wgts/cnv_tools/R/CNA_supporting_functions.r"))


test_that("log_cutoff_finder finds log cutoff", {
  expected_cutoffs = list(
    "LOG_R_HTZD" = -0.30521659411863716,
    "LOG_R_HMZD" = -1.1500465338125618,
    "LOG_R_GAIN" = 0.21380308639094972,
    "LOG_R_AMPL" = 0.5923147096446795
  )
  expect_equal(log_r_cutoff_finder(0.69), expected_cutoffs)
}
)


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
            
            arm_level_calls <- arm_level_caller_sequenza(seg=segs, centromeres=centromeres, gain_threshold=gain_threshold, shallow_deletion_threshold=shallow_deletion_threshold, seg.perc.threshold=0.5)
            expect_equal(arm_level_calls, expected_arm_level_calls)
            
          }
)


##TODO: Add test for preProcCNA()
##TODO: test purple file  e.g."OCT_011418_Bl_P_OCT_011418-TS.purple.cnv.somatic.tsv"

