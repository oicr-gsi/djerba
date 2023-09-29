
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
  make_option(c("-y", "--seqtype"), type="character", default="GENOME", help="sequencing type", metavar="character"),
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
     write.table(df_cbio_filt, file=paste0(outdir, "/data_mutations_extended.txt"), sep="\t", row.names=FALSE, quote=FALSE)
     write.table(df_cbio_filt, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
   } else {

    # for cbioportal input
    write.table(df_cbio_filt, file=paste0(outdir, "/data_mutations_extended.txt"), sep="\t", row.names=FALSE, quote=FALSE)

    # subset to oncokb annotated genes
    df_cbio_filt_oncokb <- subset(df_cbio_filt, ONCOGENIC == "Oncogenic" | ONCOGENIC == "Likely Oncogenic")
    if ( dim(df_cbio_filt_oncokb)[[1]] == 0 ) {
      print("no oncogenic mutations, shooting a blank")
      write.table(df_cbio_filt_oncokb, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
    } else {

      # write the oncogenic table
      write.table(df_cbio_filt_oncokb, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
    }
  }
 }
