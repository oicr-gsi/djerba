addVAFtoMAF <- function(maf_df, alt_col, dep_col, vaf_header) {
  
  # print a warning if any values are missing (shouldn't happen), but change them to 0
  if(anyNA(maf_df[[alt_col]]) || anyNA(maf_df[[dep_col]])) {
    print("Warning! Missing values found in one of the count columns")
    maf_df[[alt_col]][is.na(maf_df[[alt_col]])] <- 0
    maf_df[[dep_col]][is.na(maf_df[[dep_col]])] <- 0
  }
  
  # ensure factors end up as numeric
  maf_df[[alt_col]] <- as.numeric(as.character(maf_df[[alt_col]]))
  maf_df[[dep_col]] <- as.numeric(as.character(maf_df[[dep_col]]))
  
  # ensure position comes after alternate count field
  bspot                  <- which(names(maf_df)==alt_col)
  maf_df                 <- data.frame(maf_df[1:bspot], vaf_temp=maf_df[[alt_col]]/maf_df[[dep_col]], maf_df[(bspot+1):ncol(maf_df)], check.names=FALSE)
  names(maf_df)[bspot+1] <- vaf_header
  
  # check for any NAs
  if(anyNA(maf_df[[vaf_header]])) {
    print("Warning! There are missing values in the new vaf column")
    maf_df[[vaf_header]][is.na(maf_df[[vaf_header]])] <- 0
  }
  
  return(maf_df)
}

construct_whizbam_links <- function(df, whizbam_url) {

  if( dim(df)[[1]] != 0 ) {
      print("--- adding Whizbam links ---")
      df$whizbam <- paste0(whizbam_url,
                       "&chr=", gsub("chr", "", df$Chromosome),
                       "&chrloc=", paste0(df$Start_Position, "-", df$End_Position))
  } else {
      print("--- No Whizbam links added to empty file ---")
  }
  return(df)
}

procVEP <- function(maf_df){
  
  print("--- adding VAF column ---")
  
  # add vaf columns
  maf_df <- addVAFtoMAF(maf_df, "t_alt_count", "t_depth", "tumour_vaf")
  maf_df <- addVAFtoMAF(maf_df, "n_alt_count", "n_depth", "normal_vaf")
  
  print("--- adding oncogenic binary column ---")
  
  # add oncogenic yes or no columns
  df_anno <- transform(maf_df,
  oncogenic_binary = ifelse(ONCOGENIC == "Oncogenic" | ONCOGENIC == "Likely Oncogenic",
                            "YES", "NO")
  )
  
  print("--- adding common_variant binary column ---")
  
  # add common_variant yes or no columns
  df_anno <- transform(df_anno,
  ExAC_common = ifelse(grepl("common_variant", df_anno$FILTER),
                      "YES", "NO")
  )
  
  print("--- adding gnomAD_AF_POPMAX binary column ---")
  
  # add POPMAX yes or no columns
  gnomad_cols <- c("gnomAD_AFR_AF", "gnomAD_AMR_AF", "gnomAD_ASJ_AF", "gnomAD_EAS_AF", "gnomAD_FIN_AF", "gnomAD_NFE_AF", "gnomAD_OTH_AF", "gnomAD_SAS_AF")
  df_anno[gnomad_cols][is.na(df_anno[gnomad_cols])] <- 0
  df_anno[, "gnomAD_AF_POPMAX"] <- apply(df_anno[gnomad_cols], 1, max)
  
  print("--- small change to filters ---")
  # caller artifact filters
  df_anno$FILTER <- gsub("^clustered_events$",
                        "PASS",
                        df_anno$FILTER)
  
  df_anno$FILTER <- gsub("^clustered_events;common_variant$",
                        "PASS",
                        df_anno$FILTER)
  
  df_anno$FILTER <- gsub("^common_variant$",
                        "PASS",
                        df_anno$FILTER)
  
  df_anno$FILTER <- gsub(".",
                        "PASS",
                        df_anno$FILTER,
                        fixed=TRUE)
  
  # Artifact Filter
  print("--- artifact filter ---")
  df_anno <- transform(df_anno,
  TGL_FILTER_ARTIFACT = ifelse(FILTER == "PASS",
                              "PASS", "Artifact")
  )
  
  # ExAC Filter
  print("--- exac filter ---")
  df_anno <- transform(df_anno,
  TGL_FILTER_ExAC = ifelse(ExAC_common == "YES" & Matched_Norm_Sample_Barcode == "unmatched",
                          "ExAC_common", "PASS")
  )
  
  # gnomAD_AF_POPMAX Filter
  print("--- gnomAD filter ---")
  df_anno <- transform(df_anno,
  TGL_FILTER_gnomAD = ifelse(gnomAD_AF_POPMAX > 0.001 & Matched_Norm_Sample_Barcode == "unmatched",
                            "gnomAD_common", "PASS")
  )
  
  # VAF Filter
  print("--- VAF filter ---")
  df_anno <- transform(df_anno,
  TGL_FILTER_VAF = ifelse(tumour_vaf >= 0.15 | (tumour_vaf < 0.15 & oncogenic_binary == "YES"),
                          "PASS", "low_VAF")
  )
  
  # Mark filters
  print("--- printing verdict ---")
  df_anno <- transform(df_anno,
  TGL_FILTER_VERDICT = ifelse(TGL_FILTER_ARTIFACT == "PASS" & TGL_FILTER_ExAC == "PASS" & TGL_FILTER_gnomAD == "PASS" & TGL_FILTER_VAF == "PASS",
                              "PASS",
                               paste(df_anno$TGL_FILTER_ARTIFACT, df_anno$TGL_FILTER_ExAC, TGL_FILTER_gnomAD, df_anno$TGL_FILTER_VAF, sep=";"))
  )
  
  df_filt <- subset(df_anno, TGL_FILTER_VERDICT == "PASS")
  
  return(df_filt)
}

computeLOH <- function(data, purity){

  temp_table <- data %>% mutate(LHS = tumour_vaf/purity*CN)
  final_table <- temp_table %>% mutate(RHS = CN-0.5)

  final_table$LOH <- final_table$LHS > final_table$RHS & final_table$MACN <= 0.5 

  return(final_table)
}
