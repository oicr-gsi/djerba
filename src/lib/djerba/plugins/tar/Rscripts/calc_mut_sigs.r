plot_dcSigs <- function(df_snv, plotdir) {

   # fix formatting
   df_snv$Tumor_Sample_Barcode <- as.character(df_snv$Tumor_Sample_Barcode)

   # read input data
   sigs_input <- mut.to.sigs.input(mut.ref=df_snv,
                                sample.id="Tumor_Sample_Barcode",
                                chr="Chromosome",
                                pos="Start_Position",
                                ref="Reference_Allele",
                                alt="Allele",
                                bsg=BSgenome.Hsapiens.UCSC.hg38)

   # calculate a sample
   samplelist <- as.character(unique(df_snv$Tumor_Sample_Barcode))
   df_weights <- NULL
   for (sample in samplelist)
    {
       sample_sigs <- whichSignatures(tumor.ref=sigs_input,
                           signatures.ref=signatures.nature2013,
                           sample.id=sample,
                           contexts.needed=TRUE,
                           tri.counts.method='exome')

       # plot the normed value
       #png(file=paste(plotdir, "/", sample,".dcSigs_norm.png", sep=""), units="px", height=700, width=1000)
        #print({
        #    plotSignatures(sample_sigs, sub=sample)
        #})
       #dev.off()

       # get signature weights
       weights <- sample_sigs$weights
       df_weights <- rbind(df_weights, weights)
    }

return(df_weights)

}
