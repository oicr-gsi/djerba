library(testthat)

expected_cutoffs = list(
    "LOG_R_HTZD" = -0.30521659411863716,
    "LOG_R_HMZD" = -1.1500465338125618,
    "LOG_R_GAIN" = 0.21380308639094972,
    "LOG_R_AMPL" = 0.5923147096446795
  )

test_that("log_cutoff_finder finds log cutoff", {
  expect_equal(log_r_cutoff_finder(0.69), expected_cutoffs)
  }
)

maffile <- ""
maf_df <- read.csv(maffile, sep="\t", header=TRUE, check.names=FALSE, stringsAsFactors=FALSE)

test_that("procVEP processes Variant Effect Predictor file correctly",{
  procVEP(maf_df)
  }
)


## still need tests for:
  #preProcCNA(segfile, genebed, cutoffs, oncolist)
  #preProcRNA(gepfile, enscon)

