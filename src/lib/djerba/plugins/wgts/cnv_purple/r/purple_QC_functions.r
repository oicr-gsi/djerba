#' functions for QC plots of PURPLE results

library(dplyr)
library(tidyr)
library(ggplot2)
library(cowplot)
theme_set(theme_bw())

plot_purity_range <- function(rangeDF){
  #forked from hmftools/purple/src/main/resources/r/copyNumberPlots.R on Aug 19th 2022
  
  library(ggplot2)
  library(dplyr)
  
  bestPurity = rangeDF[1, "purity"]
  bestPloidy = rangeDF[1, "ploidy"]
  bestScore = rangeDF[1, "score"]
  
  range_after =  rangeDF %>%
    arrange(purity, ploidy) %>%
    group_by(purity) %>%
    mutate(
      absScore = pmin(4, score),
      score = pmin(1, abs(score - bestScore) / score),
      leftPloidy = lag(ploidy),
      rightPloidy = lead(ploidy),
      xmin = ploidy - (ploidy - leftPloidy) / 2,
      xmax = ploidy + (rightPloidy - ploidy) / 2,
      ymin = purity - 0.005,
      ymax = purity + 0.005,
      xmin = ifelse(is.na(xmin), ploidy, xmin),
      xmax = ifelse(is.na(xmax), ploidy, xmax))
  
  maxPloidy = min(range_after %>% arrange(purity, -ploidy) %>% group_by(purity)  %>% filter(row_number() == 1) %>% select(purity, ploidy = xmax) %>% ungroup() %>% select(ploidy))
  minPloidy = max(range_after %>% arrange(purity, ploidy) %>% group_by(purity)  %>% filter(row_number() == 1) %>% select(purity, maxPloidy = xmin) %>% ungroup() %>% select(maxPloidy))
  
  maxPloidy = max(maxPloidy, bestPloidy)
  minPloidy = min(minPloidy, bestPloidy)
  
  range_after = range_after %>%
    filter(xmin <= maxPloidy, xmax >= minPloidy) %>%
    mutate(xmax = pmin(xmax, maxPloidy), xmin = pmax(xmin, minPloidy))
  
  
  range_plot <- ggplot(range_after) +
    geom_rect(aes(fill=score, xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax)) +
    
    geom_segment(aes(y = 0.085, yend = 1.05, x=bestPloidy, xend = bestPloidy), linetype = "dashed", linewidth = 0.1) +
    geom_label(data = data.frame(), aes(x = bestPloidy, y = 1.05, label = round(bestPloidy, 2)), size = 5) +
    geom_segment(aes(y = bestPurity, yend = bestPurity, x=minPloidy, xend = maxPloidy + 0.4), linetype = "dashed", linewidth = 0.1) +
    geom_label(data = data.frame(), aes(y = bestPurity, x = maxPloidy + 0.4, label = paste0(bestPurity*100,"%" )), size = 5, hjust = 0.7) +
    
    
    scale_y_continuous(labels = c("30%", "50%", "75%", "100%"), breaks = c(0.3, 0.5, 0.75, 1)) +
    scale_fill_gradientn(colours=c("black","darkblue","blue", "lightblue",  "white", "white"), limits = c(0, 1), values=c(0,0.1, 0.1999, 0.2, 0.5, 1), breaks = c(0.1,0.25, 0.5, 1), labels = c("10%","25%", "50%", "100%"), name = "Relative\nScore") +
    xlab("Ploidy") + ylab("Cellularity") + theme_bw(base_size=18) +
    theme(panel.grid = element_blank()) 
  
  return(range_plot)
  
}
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
  
  png(paste0(dir_path,"/purple.segment_QC.png"), width = 1000, height = 1600, res = 300)

    print(
      plot_grid(pgrid, legend, ncol = 2, rel_widths = c(.9, .1))
    )
  
  dev.off()

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

plot_purity_range <- function(rangeDF){
  #forked from hmftools/purple/src/main/resources/r/copyNumberPlots.R on Aug 19th 2022
  
  library(ggplot2)
  library(dplyr)
  
  bestPurity = rangeDF[1, "purity"]
  bestPloidy = rangeDF[1, "ploidy"]
  bestScore = rangeDF[1, "score"]
  
  range_after =  rangeDF %>%
    arrange(purity, ploidy) %>%
    group_by(purity) %>%
    mutate(
      absScore = pmin(4, score),
      score = pmin(1, abs(score - bestScore) / score),
      leftPloidy = lag(ploidy),
      rightPloidy = lead(ploidy),
      xmin = ploidy - (ploidy - leftPloidy) / 2,
      xmax = ploidy + (rightPloidy - ploidy) / 2,
      ymin = purity - 0.005,
      ymax = purity + 0.005,
      xmin = ifelse(is.na(xmin), ploidy, xmin),
      xmax = ifelse(is.na(xmax), ploidy, xmax))
  
  maxPloidy = min(range_after %>% arrange(purity, -ploidy) %>% group_by(purity)  %>% filter(row_number() == 1) %>% select(purity, ploidy = xmax) %>% ungroup() %>% select(ploidy))
  minPloidy = max(range_after %>% arrange(purity, ploidy) %>% group_by(purity)  %>% filter(row_number() == 1) %>% select(purity, maxPloidy = xmin) %>% ungroup() %>% select(maxPloidy))
  
  maxPloidy = max(maxPloidy, bestPloidy)
  minPloidy = min(minPloidy, bestPloidy)
  
  range_after = range_after %>%
    filter(xmin <= maxPloidy, xmax >= minPloidy) %>%
    mutate(xmax = pmin(xmax, maxPloidy), xmin = pmax(xmin, minPloidy))
  
  
  range_plot <- ggplot(range_after) +
    geom_rect(aes(fill=score, xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax)) +
    
    geom_segment(aes(y = 0.085, yend = 1.05, x=bestPloidy, xend = bestPloidy), linetype = "dashed", linewidth = 0.1) +
    geom_label(data = data.frame(), aes(x = bestPloidy, y = 1.05, label = round(bestPloidy, 2)), size = 5) +
    geom_segment(aes(y = bestPurity, yend = bestPurity, x=minPloidy, xend = maxPloidy + 0.4), linetype = "dashed", linewidth = 0.1) +
    geom_label(data = data.frame(), aes(y = bestPurity, x = maxPloidy + 0.4, label = paste0(bestPurity*100,"%" )), size = 5, hjust = 0.7) +
    
    
    scale_y_continuous(labels = c("30%", "50%", "75%", "100%"), breaks = c(0.3, 0.5, 0.75, 1)) +
    scale_fill_gradientn(colours=c("black","darkblue","blue", "lightblue",  "white", "white"), limits = c(0, 1), values=c(0,0.1, 0.1999, 0.2, 0.5, 1), breaks = c(0.1,0.25, 0.5, 1), labels = c("10%","25%", "50%", "100%"), name = "Relative\nScore") +
    xlab("Ploidy") + ylab("Cellularity") + theme_bw(base_size=18) +
    theme(panel.grid = element_blank()) 
  
  return(range_plot)
  
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
