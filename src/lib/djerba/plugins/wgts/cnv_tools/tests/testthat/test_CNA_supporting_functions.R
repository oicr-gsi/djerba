library(testthat)

basedir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), sep='/')
testdatadir <- paste(Sys.getenv(c("DJERBA_TEST_DATA")), sep='/')

source(paste0(basedir, "/plugins/wgts/cnv_tools/R/CNA_supporting_functions.r"))

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

##TODO: Add test for preProcCNA()
