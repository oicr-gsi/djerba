
library(ggplot2)
library(dplyr)
theme_set(theme_bw())
library(tidyr)
library(cowplot)


alleleDeviation <- function(purity, normFactor, ploidy, standardDeviation = 0.05, minStandardDeviationPerPloidyPoint = 1.5) {
  ploidyDistanceFromInteger = 0.5
  if (ploidy > -0.5) {
    ploidyDistanceFromInteger = abs(ploidy - round(ploidy))
  }
  
  standardDeviationsPerPloidy = max(minStandardDeviationPerPloidyPoint, purity * normFactor / 2/ standardDeviation)
  return (2 * pnorm(ploidyDistanceFromInteger * standardDeviationsPerPloidy) - 1 + max(-0.5-ploidy,0))
}


clonality_plot <- function(somaticBuckets, clonalityModel) {
  clonalityVariants = somaticBuckets %>% group_by(variantCopyNumberBucket) %>% summarise(count = sum(count))
  
  subclonalPercentage = clonalityModel %>% 
    group_by(bucket) %>% 
    mutate(totalWeight = sum(bucketWeight)) %>% 
    filter(isSubclonal) %>%
    summarise(
      isSubclonal = T,
      bucketWeight = sum(bucketWeight), 
      subclonalLikelihood = ifelse(bucketWeight == 0, 0, bucketWeight / max(totalWeight)))
  
  nonResidualModel = clonalityModel %>% filter(peak != 0)
  
  nonResidualSubclonalPercentage = nonResidualModel %>%
    group_by(bucket) %>%
    mutate(totalWeight = sum(bucketWeight)) %>%
    filter(isSubclonal) %>%
    summarise(
      isSubclonal = T,
      bucketWeight = sum(bucketWeight),
      subclonalLikelihood = ifelse(bucketWeight == 0, 0, bucketWeight / max(totalWeight)))
  
  combinedModel = nonResidualModel %>%
    group_by(bucket) %>% 
    summarise(bucketWeight = sum(bucketWeight))
  
  singleBlue = "#6baed6"
  singleRed = "#d94701"
  
  pTop = ggplot() +
    geom_bar(data=clonalityVariants, aes(x = variantCopyNumberBucket, weight = count), fill=singleBlue, col=singleBlue,  alpha = .4, size = 0.07, width = 0.05) +
    geom_line(data=combinedModel , aes(x = bucket, y = bucketWeight), position = "identity", alpha = 0.8) +
    geom_line(data=nonResidualModel, aes(x = bucket, y = bucketWeight, color = peak), position = "identity") +
    geom_area(data=nonResidualSubclonalPercentage %>% filter(isSubclonal), aes(x = bucket, y = bucketWeight), position = "identity",  alpha = 0.3, fill = singleRed, color = singleRed) +
    ggtitle("") + xlab("") + ylab("Number of Variants") +
    scale_y_continuous(expand=c(0.02, 0.02)) +
    theme(panel.border = element_blank(), panel.grid.minor = element_blank(), axis.ticks = element_blank(), legend.position="none") +
    scale_x_continuous( expand=c(0.01, 0.01), limits = c(0, 3.5)) 
  
  pBottom = ggplot(data = subclonalPercentage) +
    geom_bar(width = 0.05, aes(x = bucket, y = subclonalLikelihood), stat = "identity", fill=singleRed, col=singleRed,  alpha = 0.3) + 
    theme(panel.border = element_blank(), panel.grid.minor = element_blank(), axis.ticks = element_blank()) +
    xlab("Variant Copy Number") + ylab("L(subclonal)") +
    scale_y_continuous(labels = c("0%", "25%","50%","75%","100%"), breaks = c(0, 0.25, 0.5, 0.75, 1), expand=c(0.02, 0.02), limits = c(0, 1)) +
    scale_x_continuous( expand=c(0.01, 0.01), limits = c(0, 3.5)) 
  
  print(
    cowplot::plot_grid(pTop, pBottom, ncol = 1, rel_heights = c(5, 1), align = "v")
  )
}

wholeGenomeDoublingDistanceCalculator <- function(majorAllele, minorAllele){
  wholeGenomeDoublingDistance = 1 + (abs(majorAllele - 2)) + (abs(minorAllele - 2))
  return(wholeGenomeDoublingDistance)
}

singleEventDistanceCalculator <- function(majorAllele, minorAllele){
  singleEventDistance = (abs(majorAllele - 1)) + (abs(minorAllele - 1))
  return(singleEventDistance)
}

eventPenalty <- function(majorAllele, minorAllele, ploidyPenaltyFactor = 0.4) {
  wholeGenomeDoublingDistance = wholeGenomeDoublingDistanceCalculator(majorAllele, minorAllele)
  singleEventDistance = singleEventDistanceCalculator(majorAllele, minorAllele)
    
  return (1 + ploidyPenaltyFactor * min(singleEventDistance, wholeGenomeDoublingDistance))
}


majorAlleleDeviation <- function(purity, normFactor, ploidy, baselineDeviation, majorAlleleSubOnePenaltyMultiplier = 1 ) {
  majorAlleleMultiplier = 1
  if (ploidy > 0 && ploidy < 1) {
    majorAlleleMultiplier = pmax(1,majorAlleleSubOnePenaltyMultiplier*(1-ploidy))
  }
  
  deviation = majorAlleleMultiplier * alleleDeviation(purity, normFactor, ploidy) + subMininimumPloidyPenalty(1, ploidy)
  return (max(deviation, baselineDeviation))
}

minorAlleleDeviation <- function(purity, normFactor, ploidy, baselineDeviation) {
  deviation = alleleDeviation(purity, normFactor, ploidy) + subMininimumPloidyPenalty(0, ploidy)
  return (max(deviation, baselineDeviation))
}

purityDataFrame <- function(mat, ploidy) {
  df = cbind(majorAllele = ploidy, data.frame(mat))
  colnames(df) <- c("MajorAllele", ploidy)
  df = df %>% gather(MinorAllele, Penalty, -MajorAllele) %>%
    filter(!is.na(Penalty)) %>%
    mutate(MinorAllele = as.numeric(MinorAllele), MajorAllele = as.numeric(MajorAllele))
  
  return (df)
}

purityMatrix <- function(purity, ploidy, baselineDeviation = 0.1) {
  resultMatrix = matrix(nrow = length(ploidy), ncol = length(ploidy))
  for (i in c(1:length(ploidy))){
    #cat (i, " ")
    for (j in c(1:i)){
      majorPloidy = ploidy[i]
      minorPloidy = ploidy[j]
      totalPenalty = eventPenalty(majorPloidy, minorPloidy) *
                      (majorAlleleDeviation(purity, 1, majorPloidy, baselineDeviation) + 
                        minorAlleleDeviation(purity, 1, minorPloidy, baselineDeviation)) 
      resultMatrix[i,j] = totalPenalty
    }
  }
  
  return (resultMatrix)
}


subMininimumPloidyPenalty <- function(minPloidy, ploidy, majorAlleleSubOneAdditionalPenalty = 1.5) {
  penalty = - majorAlleleSubOneAdditionalPenalty * (ploidy - minPloidy)
  return (min(majorAlleleSubOneAdditionalPenalty, max(penalty, 0)))
}




look_at_purity_fit <- function(sample, this_purity, purpleDir='~/Desktop') {
  
  somatic_file_name = paste0(purpleDir, "/", sample, ".purple.somatic.hist.tsv")
  
  if(file.exists(somatic_file_name)){
    somaticBuckets = read.table(somatic_file_name, sep = "\t", header = T, numerals = "no.loss", skipNul = T)
    clonalityModel = read.table(paste0(purpleDir, "/", sample, ".purple.somatic.clonality.tsv"), sep = "\t", header = T, numerals = "no.loss", skipNul = T) %>%
      mutate(isSubclonal = isSubclonal == "true", isValid = isValid == "true", peak = as.character(peak), bucketWeight = as.numeric(as.character(bucketWeight))) %>% filter(isValid)
    
    clonality_plot(somaticBuckets, clonalityModel)
  }
  
  
  fittedSegmentsDF = read.table(file = paste0(purpleDir, "/", sample, ".purple.segment.tsv"), sep = "\t", header = T, comment.char = "!")

  fittedSegmentsDF = fittedSegmentsDF %>%
  filter(germlineStatus == "DIPLOID", bafCount > 0) %>%
    arrange(majorAlleleCopyNumber) %>%
    
  mutate(
    Score = deviationPenalty * eventPenalty,
    Weight = bafCount
    )


  maxData = fittedSegmentsDF %>%  select(majorAlleleCopyNumber, Score)
  
  maxScore = ceiling(max(maxData$Score))
  minScore = floor(min(maxData$Score))
  maxMajorAllelePloidy = ceiling(max(maxData$majorAlleleCopyNumber))
  maxMinorAllelePloidy = maxMajorAllelePloidy - 1
  
  
  sim_ploidy_series = seq(-1, maxMajorAllelePloidy, by = 0.01)
  
  PurityDF = purityDataFrame(
                purityMatrix(this_purity, sim_ploidy_series), 
                sim_ploidy_series)
  
  
  fittedSegmentsDF$SingleEventDistance <- singleEventDistanceCalculator(fittedSegmentsDF$majorAlleleCopyNumber, fittedSegmentsDF$minorAlleleCopyNumber)
  fittedSegmentsDF$WholeGenomeDoublingDistance <- wholeGenomeDoublingDistanceCalculator(fittedSegmentsDF$majorAlleleCopyNumber, fittedSegmentsDF$minorAlleleCopyNumber)
  
 
  penalty_breakdown_plot <- 
    ggplot(fittedSegmentsDF,aes(x=WholeGenomeDoublingDistance, y=SingleEventDistance, color=Score)) + 
      geom_point(aes( size=Weight),shape=1) + 
      geom_abline(slope = 1, alpha=0.5,linetype="dashed") +
      scale_color_gradientn(colours=c("blue","green","yellow","orange", "red"), limits = c(minScore, maxScore), na.value = "lightgrey") +
      labs(x="Whole Genome Doubling Penalty", y="Single Event Penalty", size="BAF Support") +
       coord_fixed() + guides(size="none", color="none")

  
  sim_penalty_plot <- 
  ggplot() +
    geom_tile(data=PurityDF,aes(x = MajorAllele, y = MinorAllele,  fill = Penalty)) +
    geom_point(data=fittedSegmentsDF , aes(y=minorAlleleCopyNumber, x=majorAlleleCopyNumber, size=Weight),shape=1) + 
    geom_abline(slope = 1) +
    scale_x_continuous(breaks = c(-200:200), limits = c(0, maxMajorAllelePloidy)) +
    scale_y_continuous(breaks = c(-200:200), limits = c(0, maxMinorAllelePloidy)) +

    scale_fill_gradientn(colours=c("blue","green","yellow","orange", "red"), limits = c(minScore, maxScore), na.value = "white") +
    theme(
      panel.grid = element_blank()
    ) +
    coord_fixed()+
    labs(x="Major Allele Ploidy", y="Minor Allele Ploidy", fill="Aggregate\nPenalty",size="BAF\nSupport")

  
  
  legend <- get_legend(sim_penalty_plot)
  sim_penalty_plot <- sim_penalty_plot  + guides(size='none',fill='none')
  
  # build grid without legends
  pgrid <- plot_grid(penalty_breakdown_plot, sim_penalty_plot,  ncol = 1)

  
  print(
  plot_grid(pgrid, legend, ncol = 2, rel_widths = c(.9, .1))
  )
  
  
  
  ## From PURPLE documentation
  # An average is calculated for each value, weighted by the number of BAF observations in each segment. 
  mean_singleEvent = mean(fittedSegmentsDF$SingleEventDistance * fittedSegmentsDF$Weight)
  mean_WGD = mean(fittedSegmentsDF$WholeGenomeDoublingDistance * fittedSegmentsDF$Weight)
  
  # The averaged numbers are multiplied by each other to form an overall ploidy penalty for the sample.
  overall_sample_penalty = mean_singleEvent * mean_WGD
  #cat("Overall Sample Penalty: ", overall_sample_penalty, "\n")
  
  return(fittedSegmentsDF)
}

 
fitted_segments = look_at_purity_fit(sample = "purity_min_7", this_purity = 0.87) 
fitted_segments = look_at_purity_fit("purity_min_0", 0.27) 





