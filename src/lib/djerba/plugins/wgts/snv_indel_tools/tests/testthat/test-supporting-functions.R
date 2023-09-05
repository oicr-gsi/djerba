library(testthat)
basedir="/Volumes/cgi/scratch/fbeaudry/reporting/djerba/src/lib/djerba/snv_indel_tools"
source(paste0(basedir, "/R/supporting_functions.r"))

expected_cutoffs = list(
    "LOG_R_HTZD" = -0.30521659411863716,
    "LOG_R_HMZD" = -1.1500465338125618,
    "LOG_R_GAIN" = 0.21380308639094972,
    "LOG_R_AMPL" = 0.5923147096446795
  )

test_that("log_cutoff_finder finds log cutoff", {
  expect_equal(log_r_cutoff_finder(0.69), expected_cutoffs)
  expect_equal(log_r_cutoff_finder(1), expected_cutoffs)
  }
)

maffile <- "/Volumes/cgi/scratch/fbeaudry/reporting/djerba_test/plugins/wgts/tmp/annotated_maf.tsv"
maf_df <- read.csv(maffile, sep="\t", header=TRUE, check.names=FALSE, stringsAsFactors=FALSE)

test_that("procVEP processes Variant Effect Predictor file correctly",{
  processed_maf <- procVEP(maf_df)
  }
)


## still need tests for:
  #preProcCNA(segfile, genebed, cutoffs, oncolist)
  #preProcRNA(gepfile, enscon)

