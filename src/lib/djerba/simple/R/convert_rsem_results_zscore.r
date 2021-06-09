# preprocess function
preProcRNA <- function(gepfile, enscon, genelist = NULL){
 
 # testing:
 #gepfile="T:/gsi/jtorchia/pipeline/data/OCTCAP/cbioportal/cBioWrap_20200204/output/gepdir/input.fpkm.txt"
 #enscon="T:/gsi/jtorchia/git/cBioWrap/files/ensemble_conversion.txt"
 #genelist="T:/gsi/jtorchia/git/cBioWrap/files/targeted_genelist.txt"

 # read in data
 gepData <- read.csv(gepfile, sep="\t", header=TRUE, check.names=FALSE)
 ensConv <- read.csv(enscon, sep="\t", header=FALSE)

 # rename columns
 colnames(ensConv) <- c("gene_id", "Hugo_Symbol")

 # merge in Hugo's, re-order columns, deduplicate
 df <- merge(x=gepData, y=ensConv, by="gene_id", all.x=TRUE)
 df <- subset(df[,c(ncol(df),2:(ncol(df)-1))], !duplicated(df[,c(ncol(df),2:(ncol(df)-1))][,1]))
 df <- df[!is.na(df$Hugo_Symbol),]
 row.names(df) <- df[,1]
 df <- df[,-1]

 # subset if gene list given
 if (!is.null(genelist)) {
	keep_genes <- readLines(genelist)
	df <- df[row.names(df) %in% keep_genes,]
 }

 # return the data frame
 return(df)
}

# simple zscore function
compZ <- function(df) {

 # scale row-wise
 df_zscore <- t(scale(t(df)))

 # NaN (when SD is 0) becomes 0
 df_zscore[is.nan(df_zscore)] <- 0

 # we want a dataframe
 df_zscore <- data.frame(signif(df_zscore, digits=4), check.names=FALSE)

 return(df_zscore)
}
