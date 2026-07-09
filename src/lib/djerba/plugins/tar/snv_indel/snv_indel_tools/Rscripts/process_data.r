
rm(list=ls())
library(CNTools)
library(optparse)
library(BSgenome.Hsapiens.UCSC.hg38)
library(deconstructSigs)

# command line options
option_list = list(
  make_option(c("-a", "--basedir"), type="character", default=NULL, help="cBioWrap base directory", metavar="character"),
  make_option(c("-f", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-b", "--maffile"), type="character", default=NULL, help="concatenated maf file", metavar="character"),
  make_option(c("-C", "--cbiostudy"), type="character", default='None', help="cbioportal studyid", metavar="character"),
  make_option(c("-u", "--whizbam_url"), type="character", default="https://whizbam.oicr.on.ca", help="whizbam url", metavar="character"),
  make_option(c("-w", "--tumourid"), type="character", default=NULL, help="whizbam tumour name", metavar="character"),
  make_option(c("-x", "--normalid"), type="character", default=NULL, help="whizbam normal name", metavar="character"),
  make_option(c("-y", "--seqtype"), type="character", default="EXOME", help="sequencing type", metavar="character"),
  make_option(c("-z", "--genome"), type="character", default="hg38", help="genome version", metavar="character"),
  make_option(c("-T", "--tar"), type="character", default=FALSE, help="true or false value for tar assay", metavar="boolean")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE);
opt <- parse_args(opt_parser);

# set better variable names
basedir <- opt$basedir
outdir <- opt$outdir
maffile <- opt$maffile
studyid <- opt$studyid
whizbam_url <- opt$whizbam_url
tumourid <- opt$tumourid
normalid <- opt$normalid
seqtype <- opt$seqtype
genome <- opt$genome
tar <- opt$tar
cbio_study <- opt$cbiostudy


# print options to output
print("Running singleSample with the following options:")
print(opt)

# source functions
source(paste0(basedir, "/supporting_functions.r"))

###################### VEP #####################

if (is.null(maffile)) {
   print("No MAF file input, processing omitted")
  } else {
   print("Processing Mutation data")

   # annotate with filters
   df_cbio_anno <- procVEP(maffile)
   # add whizbam links
   df_cbio_anno_whizbam <- construct_whizbam_links(df_cbio_anno, whizbam_url, cbio_study, tumourid, normalid, seqtype, genome)

   # get pass
   df_cbio_filt <- subset(df_cbio_anno_whizbam, TGL_FILTER_VERDICT == "PASS")
   if ( dim(df_cbio_filt)[[1]] == 0 ) {
     print("No passed mutations, shooting blanks")
     # construct a dummy row for data_mutations_extended.txt and data_mutations_extended_oncogenic.txt
     # this ensures a whizbam link is always present even if there are no reportable mutations
     tumor_lib <- paste0(tumourid, "_Pl")
     tumor_file <- paste0(tumourid, "_Pl.bam")
     normal_lib <- paste0(normalid, "_BC")
     normal_file <- paste0(normalid, "_BC.bam")
     default_whizbam <- paste0(whizbam_url,
                        "/igv?project1=", cbio_study,
                        "&library1=", tumor_lib,
                        "&file1=", tumor_file,
                        "&seqtype1=", seqtype,
                        "&project2=", cbio_study,
                        "&library2=", normal_lib,
                        "&file2=", normal_file,
                        "&seqtype2=", seqtype,
                        "&chr=13&chrloc=32340212-32340213&genome=", genome)
     df_dummy <- df_cbio_filt
     df_dummy[1, ] <- NA
     df_dummy$whizbam[1] <- default_whizbam
     write.table(df_dummy, file=paste0(outdir, "/data_mutations_extended.txt"), sep="\t", row.names=FALSE, quote=FALSE)
     write.table(df_dummy, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
   } else {

    # for cbioportal input
    write.table(df_cbio_filt, file=paste0(outdir, "/data_mutations_extended.txt"), sep="\t", row.names=FALSE, quote=FALSE)

    # subset to oncokb annotated genes
    df_cbio_filt_oncokb <- subset(df_cbio_filt, ONCOGENIC == "Oncogenic" | ONCOGENIC == "Likely Oncogenic")
    if ( dim(df_cbio_filt_oncokb)[[1]] == 0 ) {
      print("no oncogenic mutations, shooting a blank")
      # construct a dummy row for data_mutations_extended_oncogenic.txt
      # this ensures a whizbam link is always present even if there are no reportable mutations
      tumor_lib <- paste0(tumourid, "_Pl")
      tumor_file <- paste0(tumourid, "_Pl.bam")
      normal_lib <- paste0(normalid, "_BC")
      normal_file <- paste0(normalid, "_BC.bam")
      default_whizbam <- paste0(whizbam_url,
                        "/igv?project1=", cbio_study,
                        "&library1=", tumor_lib,
                        "&file1=", tumor_file,
                        "&seqtype1=", seqtype,
                        "&project2=", cbio_study,
                        "&library2=", normal_lib,
                        "&file2=", normal_file,
                        "&seqtype2=", seqtype,
                        "&chr=13&chrloc=32340212-32340213&genome=", genome)
      df_dummy <- df_cbio_filt[1, ]
      df_dummy[1, ] <- NA
      df_dummy$whizbam[1] <- default_whizbam
      write.table(df_dummy, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
    } else {

      # write the oncogenic table
      write.table(df_cbio_filt_oncokb, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
    }
  }
 }
