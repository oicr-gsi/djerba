
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

eventPenalty <- function(majorAllele, minorAllele, ploidyPenaltyFactor = 0.4) {
  wholeGenomeDoublingDistance = wholeGenomeDoublingDistanceCalculator(majorAllele, minorAllele)
  singleEventDistance = singleEventDistanceCalculator(majorAllele, minorAllele)
    
  return (1 + ploidyPenaltyFactor * min(singleEventDistance, wholeGenomeDoublingDistance))
}

look_at_purity_fit <- function(segment_file, this_purity) {
  
  fittedSegmentsDF = read.table(file = segment_file, sep = "\t", header = T, comment.char = "!")
  
  fittedSegmentsDF = fittedSegmentsDF %>%
    filter(germlineStatus == "DIPLOID", bafCount > 0) %>%
    arrange(majorAlleleCopyNumber) %>%
    
    mutate(
      Score = deviationPenalty * eventPenalty,
      Weight = bafCount
    )
  
  
  maxData = fittedSegmentsDF %>%  select(majorAlleleCopyNumber, Score) %>% filter(majorAlleleCopyNumber < 5)
  
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
    scale_color_gradientn(colours=c("darkred","red","orange","yellow", "white"), limits = c(minScore, maxScore), na.value = "lightgrey") +
    labs(x="Whole Genome Doubling Penalty (log)", y="Single Event Penalty (log)", size="BAF Support") +
    #coord_fixed() + 
    guides(size="none", color="none")+ 
    scale_x_continuous(trans='log10') +
    scale_y_continuous(trans='log10')
  
  
  
  sim_penalty_plot <- 
    ggplot() +
    geom_tile(data=PurityDF,aes(x = MajorAllele, y = MinorAllele,  fill = Penalty)) +
    geom_point(data=fittedSegmentsDF , aes(y=minorAlleleCopyNumber, x=majorAlleleCopyNumber, size=Weight),shape=1) + 
    geom_abline(slope = 1) +
    scale_x_continuous(limits = c(0, min(maxMinorAllelePloidy,4))) +
    scale_y_continuous( limits = c(0, min(maxMinorAllelePloidy,3))) +
    
    scale_fill_gradientn(colours=c("darkred","red","orange","yellow", "white"), limits = c(minScore, maxScore), na.value = "white") +
    theme(
      panel.grid = element_blank()
    ) +
    coord_fixed()+
    labs(x="Major Allele Ploidy", y="Minor Allele Ploidy", fill="Aggregate\nPenalty",size="BAF\nSupport")
  
  legend <- get_legend(sim_penalty_plot)
  sim_penalty_plot <- sim_penalty_plot  + guides(size='none',fill='none')
  
  # build grid without legends
  pgrid <- plot_grid( sim_penalty_plot, penalty_breakdown_plot,  ncol = 1)
  
  svg(paste0(dir_path,"/purple.segment_QC.svg"), width = 8, height = 8)

    print(
      plot_grid(pgrid, legend, ncol = 2, rel_widths = c(.9, .1))
    )
  
  dev.off()
  
  ## From PURPLE documentation
  # An average is calculated for each value, weighted by the number of BAF observations in each segment. 
  # mean_singleEvent = mean(fittedSegmentsDF$SingleEventDistance * fittedSegmentsDF$Weight)
  # mean_WGD = mean(fittedSegmentsDF$WholeGenomeDoublingDistance * fittedSegmentsDF$Weight)
  
  # The averaged numbers are multiplied by each other to form an overall ploidy penalty for the sample.
  # overall_sample_penalty = mean_singleEvent * mean_WGD
  # cat("Overall Sample Penalty: ", overall_sample_penalty, "\n")
  
  #return(fittedSegmentsDF)
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

singleEventDistanceCalculator <- function(majorAllele, minorAllele){
  singleEventDistance = (abs(majorAllele - 1)) + (abs(minorAllele - 1))
  return(singleEventDistance)
}

subMininimumPloidyPenalty <- function(minPloidy, ploidy, majorAlleleSubOneAdditionalPenalty = 1.5) {
  penalty = - majorAlleleSubOneAdditionalPenalty * (ploidy - minPloidy)
  return (min(majorAlleleSubOneAdditionalPenalty, max(penalty, 0)))
}

wholeGenomeDoublingDistanceCalculator <- function(majorAllele, minorAllele){
  wholeGenomeDoublingDistance = 1 + (abs(majorAllele - 2)) + (abs(minorAllele - 2))
  return(wholeGenomeDoublingDistance)
}
