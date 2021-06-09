rm(list=ls())
library(CNTools)
library(optparse)
library(deconstructSigs)
library(BSgenome.Hsapiens.UCSC.hg38)

# command line options
option_list = list(
  make_option(c("-a", "--basedir"), type="character", default=NULL, help="cBioWrap base directory", metavar="character"),
  make_option(c("-b", "--maffile"), type="character", default=NULL, help="concatenated maf file", metavar="character"),
  make_option(c("-c", "--segfile"), type="character", default=NULL, help="concatenated seg file", metavar="character"),
  make_option(c("-d", "--fusfile"), type="character", default=NULL, help="concatenated fus file", metavar="character"),
  make_option(c("-e", "--gepfile"), type="character", default=NULL, help="concatenated gep file", metavar="character"),
  make_option(c("-f", "--outdir"), type="character", default=NULL, help="output directory", metavar="character"),
  make_option(c("-g", "--enscon"), type="character", default=NULL, help="ensemble conversion file", metavar="character"),
  make_option(c("-h", "--entcon"), type="character", default=NULL, help="entrez conversion file", metavar="character"),
  make_option(c("-i", "--genebed"), type="character", default=NULL, help="gene bed for segmentation", metavar="character"),
  make_option(c("-j", "--genelist"), type="character", default=NULL, help="subset cnas and rnaseq to these", metavar="character"),
  make_option(c("-k", "--oncolist"), type="character", default=NULL, help="oncoKB cancer genes", metavar="character"),
  make_option(c("-l", "--gepcomp"), type="character", default=NULL, help="samples to calculate gep against", metavar="character"),
  make_option(c("-m", "--tmbcomp"), type="character", default=NULL, help="samples to calculate tmb against", metavar="character"),
  make_option(c("-n", "--tcgadata"), type="character", default=NULL, help="tcga datadir", metavar="character"),
  make_option(c("-o", "--tcgacode"), type="character", default=NULL, help="tcga code", metavar="character"),
  make_option(c("-p", "--gain"), type="numeric", default=0.3, help="gain threshold", metavar="numeric"),
  make_option(c("-q", "--ampl"), type="numeric", default=0.7, help="amp threshold", metavar="numeric"),
  make_option(c("-r", "--htzd"), type="numeric", default=-0.3, help="htz del threshold", metavar="numeric"),
  make_option(c("-s", "--hmzd"), type="numeric", default=-0.7, help="hmz del threshold", metavar="numeric"),
  make_option(c("-t", "--minfusionreads"), type="numeric", default=20, help="minimum read support for fusions", metavar="numeric"),
  make_option(c("-u", "--whizbam_url"), type="character", default="https://whizbam.oicr.on.ca", help="whizbam url", metavar="character"),
  make_option(c("-v", "--studyid"), type="character", default=NULL, help="project id", metavar="character"),
  make_option(c("-w", "--tumourid"), type="character", default=NULL, help="whizbam tumour name", metavar="character"),
  make_option(c("-x", "--normalid"), type="character", default=NULL, help="whizbam normal name", metavar="character"),
  make_option(c("-y", "--seqtype"), type="character", default="GENOME", help="sequencing type", metavar="character"),
  make_option(c("-z", "--genome"), type="character", default="hg38", help="genome version", metavar="character")
)

# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE);
opt <- parse_args(opt_parser);

# set better variable names
basedir <- opt$basedir
maffile <- opt$maffile
segfile <- opt$segfile
fusfile <- opt$fusfile
gepfile <- opt$gepfile
outdir <- opt$outdir
enscon <- opt$enscon
entcon <- opt$entcon
genebed <- opt$genebed
genelist <- opt$genelist
oncolist <- opt$oncolist
gepcomp <- opt$gepcomp
tmbcomp <- opt$tmbcomp
tcgadata <- opt$tcgadata
tcgacode <- opt$tcgacode
gain <- opt$gain
ampl <- opt$ampl
htzd <- opt$htzd
hmzd <- opt$hmzd
minfusionreads <- opt$minfusionreads
whizbam_url <- opt$whizbam_url
studyid <- opt$studyid
tumourid <- opt$tumourid
normalid <- opt$normalid
seqtype <- opt$seqtype
genome <- opt$genome

# print options to output
print("Running singleSample with the following options:")
print(opt)

# source functions
source(paste0(basedir, "/R/convert_seg_to_gene_singlesample.r"))
source(paste0(basedir, "/R/convert_rsem_results_zscore.r"))
source(paste0(basedir, "/R/convert_vep92_to_filtered_cbio.r"))
source(paste0(basedir, "/R/convert_mavis_to_filtered_fusions.r"))
source(paste0(basedir, "/R/calc_mut_sigs.r"))

###################### VEP #####################
if (maffile == "blank") {
  } else {
   print("Processing Mutation data")

   # annotate with filters
   df_cbio_anno <- procVEP(maffile)

   # add whizbam links
   df_cbio_anno_whizbam <- construct_whizbam_links(df_cbio_anno, whizbam_url, studyid, tumourid, normalid, seqtype, genome)

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
    df_cbio_filt_oncokb <- subset(df_cbio_filt, oncogenic == "Oncogenic" | oncogenic == "Likely Oncogenic")
    if ( dim(df_cbio_filt_oncokb)[[1]] == 0 ) {
      print("no oncogenic mutations, shooting a blank")
      write.table(df_cbio_filt_oncokb, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
    } else {

      # write the oncogenic table
      write.table(df_cbio_filt_oncokb, file=paste0(outdir, "/data_mutations_extended_oncogenic.txt"), sep="\t", row.names=FALSE, quote=FALSE)
      
      # get snvs for dcsigs
      df_snv <- subset(df_cbio_filt, Variant_Type == "SNP" | Variant_Type == "DNP" | Variant_Type == "TNP")
      signdir <- paste0(outdir, "/sigs"); dir.create(signdir, showWarnings=FALSE)
      df_weights <- plot_dcSigs(df_snv, signdir)

      # write out weights
      write.table(df_weights, file=paste0(signdir, "/weights.txt"), sep="\t", quote=FALSE, row.names=TRUE, col.names=NA)

    }

   }

 }

###################### CNA #####################
print("Processing CNA data")
CNAs <- preProcCNA(segfile, genebed, gain, ampl, htzd, hmzd, genelist, oncolist)

print("writing seg file")
# segs
write.table(CNAs[[1]], file=paste0(outdir, "/data_segments.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# log2cna
print("writing log2 file")
write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[2]]), CNAs[[2]], check.names=FALSE),
  file=paste0(outdir, "/data_log2CNA.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# gistic-like file
print("writing cna file")
write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[3]]), CNAs[[3]], check.names=FALSE),
  file=paste0(outdir, "/data_CNA.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# write out the oncoKB genes
print("writing oncoKB genes")
write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[4]]), CNAs[[4]], check.names=FALSE),
  file=paste0(outdir, "/data_CNA_oncoKBgenes.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# write the truncated data_CNA file (non-zero, oncoKB genes) for oncoKB annotator
print("writing non-diploid oncoKB genes")
write.table(data.frame("Hugo_Symbol"=rownames(CNAs[[5]]), CNAs[[5]], check.names=FALSE),
  file=paste0(outdir, "/data_CNA_oncoKBgenes_nonDiploid.txt"), sep="\t", row.names=FALSE, quote=FALSE)

###################### RNASEQ - Fusions #####################
print("Processing Fusion data")

# function returns list of 3 objects ### TO WRITE
fusion_cbio <- preProcFus(fusfile, minfusionreads, entcon)

# write FUS files
print("writing fus file")
write.table(fusion_cbio[[1]], file=paste0(outdir, "/data_fusions.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# write input for oncoKB annotator
print("writing fus file for oncokb annotator")
write.table(fusion_cbio[[2]], file=paste0(outdir, "/data_fusions_oncokb.txt"), sep="\t", row.names=FALSE, quote=FALSE)

#################### RNASEQ Expression ####################
print("Processing RNASEQ data")

# preprocess the full data frame
df <- preProcRNA(gepfile, enscon, genelist)
sample <- colnames(df)[1]

print("getting CAP-level data")
# calculate z-score and percentiles TGL
df_zscore <- compZ(df)
df_percentile <- data.frame(signif(pnorm(as.matrix(df_zscore)), digits=4), check.names=FALSE)

# write zscores
write.table(data.frame(Hugo_Symbol=rownames(df_zscore), df_zscore, check.names=FALSE),
  file=paste0(outdir, "/data_expression_zscores_comparison.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# write percentiles
write.table(data.frame(Hugo_Symbol=rownames(df_percentile), df_percentile, check.names=FALSE),
  file=paste0(outdir, "/data_expression_percentile_comparison.txt"), sep="\t", row.names=FALSE, quote=FALSE)

print("getting TCGA-level data")

# get TCGA comparitor
load(file=paste(tcgadata, "/", tcgacode,".PANCAN.matrix.rdf", sep=""))
df_tcga <- get(tcgacode)

# equalize dfs (get common genes)
comg <- as.character(intersect(row.names(df_tcga), row.names(df)))
df_tcga_common <- df_tcga[row.names(df_tcga) %in% comg, ]
df_tcga_common_sort <- df_tcga_common[ order(row.names(df_tcga_common)), ]
df_stud_common <- df[row.names(df) %in% comg, ]
df_stud_common_sort <- df_stud_common[ order(row.names(df_stud_common)), ]
df_stud_tcga <- merge(df_stud_common_sort, df_tcga_common_sort, by=0, all=TRUE)
df_stud_tcga[is.na(df_stud_tcga)] <- 0
rownames(df_stud_tcga) <- df_stud_tcga$Row.names
df_stud_tcga$Row.names <- NULL
df_zscore <- compZ(df_stud_tcga)
df_zscore_sample <- data.frame(Hugo_Symbol=rownames(df_zscore), df_zscore[,1], check.names=FALSE)
df_percentile <- data.frame(signif(pnorm(as.matrix(df_zscore)), digits=4), check.names=FALSE)

# z-score TCGA
write.table(data.frame(Hugo_Symbol=rownames(df_zscore), df_zscore[sample], check.names=FALSE),
  file=paste0(outdir, "/data_expression_zscores_tcga.txt"), sep="\t", row.names=FALSE, quote=FALSE)

# percentile TCGA
write.table(data.frame(Hugo_Symbol=rownames(df_percentile), df_percentile[sample], check.names=FALSE),
  file=paste0(outdir, "/data_expression_percentile_tcga.txt"), sep="\t", row.names=FALSE, quote=FALSE)