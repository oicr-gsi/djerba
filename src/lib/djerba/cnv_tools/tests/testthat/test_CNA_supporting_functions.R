library(testthat)
basedir= Sys.getenv(c("DJERBA_BASE_DIR"))

source(paste0(basedir, "/src/lib/djerba/snv_indel_tools/R/supporting_functions.r"))

centromeres_path <- "/Volumes/cgi/scratch/fbeaudry/reporting/djerba/src/lib/djerba/data/hg38_centromeres.txt"
#purple_segfile_path <- "/Volumes/cgi/scratch/fbeaudry/validation/purple_test/diagnostic_accuracy/SVs/OCT_011418.run2/OCT_011418_Bl_P_OCT_011418-TS.purple.cnv.somatic.tsv"
sequenza_segfile_path <- "/Volumes/cgi/cap-djerba/PANXWGTS/PANX_1594/report/data_segments.txt"
gain_threshold             <- 0.146
shallow_deletion_threshold <- -0.183

segs <- read.delim(seg_file, header=TRUE) # segmented data already
segs$chrom <- paste0("chr",segs$chrom)
#names(segs) <- c("ID","chrom","loc.start", "loc.end","num.mark","seg.mean")
centromeres <- read.table(centromeres_path,header=T)

expected_arm_level_calls <- sort(c("del(21p)", "del(6q)" , "del(21q)", "del(17p)", "del(18q)", "del(6p)" , "del(9p)"))
test_that("arm_level_caller returns correct arm-level alterations", {
  arm_level_calls <- arm_level_caller(seg=segs, centromeres=centromeres, gain_threshold=gain_threshold, shallow_deletion_threshold=shallow_deletion_threshold, seg.perc.threshold=0.5)
  expect_equal(arm_level_calls, expected_arm_level_calls)
  }
)

## still need tests for:
  #preProcCNA(segfile, genebed, cutoffs, oncolist)
