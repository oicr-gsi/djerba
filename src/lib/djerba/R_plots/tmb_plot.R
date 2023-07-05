#! /usr/bin/env Rscript

# plotting code from https://github.com/oicr-gsi/djerba/blob/75149f1a2caefe25ba6ad5b9cc5f47b26f35a574/src/lib/djerba/R_markdown/html_report_default.Rmd#L497

library(dplyr)
library(ggplot2)
library(optparse)
library(scales)

option_list = list(
    make_option(c("-c", "--code"), type="character", default=NULL, help="TCGA code", metavar="character"),
    make_option(c("-o", "--output"), type="character", default=NULL, help="SVG output path", metavar="character"),
    make_option(c("-t", "--tmb"), type="numeric", default=NULL, help="TMB per Mb", metavar="numeric")
)
# get options
opt_parser <- OptionParser(option_list=option_list, add_help_option=FALSE)
opt <- parse_args(opt_parser)
sampleTMB <- opt$tmb
sample_tcga <- opt$code
out_path <- opt$output

data_dir <- paste(Sys.getenv(c("DJERBA_BASE_DIR")), 'data', sep='/')

## test
#data_dir <- "Documents/GitHub/djerba/src/lib/djerba/data/"
#out_path <- "~/"
#sampleTMB <- 7
#sample_tcga <- "PAAD"

external_tmb_file <- paste(data_dir, 'tmbcomp-externaldata.txt', sep='/')
external_tmb_data <- read.delim(external_tmb_file, header = TRUE, stringsAsFactors = F)
tcga_tmb_file <- paste(data_dir, 'tmbcomp-tcga.txt', sep='/')
tcga_tmb_data <- read.delim(tcga_tmb_file, header = TRUE, stringsAsFactors = F)

#subset external data to cancer type
external_tmb_data_type <- external_tmb_data %>% filter(if (sample_tcga %in% external_tmb_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)
#subset tcga data to cancer type
tcga_tmb_data_type <- tcga_tmb_data %>% filter(if (sample_tcga %in% tcga_tmb_data$CANCER.TYPE) CANCER.TYPE == sample_tcga else NA)

label_location <- max(density(tcga_tmb_data$tmb)$y)
if(length(external_tmb_data_type$tmb) > 0){
  tmp_max <- max(density(external_tmb_data_type$tmb)$y)
  label_location <- max(label_location,tmp_max)
}
if(length(tcga_tmb_data_type$tmb) > 0){
  tmp_max <- max(density(tcga_tmb_data_type$tmb)$y)
  label_location <- max(label_location,tmp_max)
}

options(bitmapType='cairo')
svg(out_path, width=8, height=3)
ggplot(tcga_tmb_data, aes(tmb)) +
  geom_density(aes(fill = "All TCGA"), alpha = 0.5) + 
  scale_x_continuous(expand = c(0, 0), limit = c(0, max(sampleTMB, 25))) +
  scale_y_continuous(expand = c(0, 0),labels = percent) +
  coord_cartesian(xlim = c(0, max(sampleTMB, 25)),
                  clip = 'off') +
  
  geom_vline(xintercept = sampleTMB,linetype="solid",colour = "black")+
  geom_vline(xintercept = 10,linetype="longdash",colour = "red") +
  
  annotate(y=label_location,geom="text",x = sampleTMB, color="black",label="This tumour", hjust = -0.02,size=5,vjust=2) +
  annotate(y=label_location,geom="text",x = 10,color="red",label="TMB-H threshold", hjust =-0.02,size=5) +
  
  xlab("Coding Mutations per Mb") +
  ylab("% of samples") +
  {
    if (sample_tcga %in% external_tmb_data_type$CANCER.TYPE)
      geom_density(data = external_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
    else if (sample_tcga %in% tcga_tmb_data_type$CANCER.TYPE)
      geom_density(data = tcga_tmb_data_type, aes(fill = "Cohort"), alpha = 0.5)
  } + scale_fill_discrete(name = "Cohort") +
  theme_classic() + 
  theme(text = element_text(size = 25),
        plot.margin = unit(c(1, 1, 1, 1), "lines"),
        panel.grid = element_blank(), 
        line = element_blank(),
        legend.background = element_rect(fill='transparent')
  )

dev.off()

median_tmb <- median(tcga_tmb_data$tmb)
svg(out_path, width = 5, height = 1)

ggplot(tcga_tmb_data) + 
  geom_boxplot(aes(x=0,y=tmb,color="All TCGA"),width = 0.05, outlier.shape = NA) +
  
  geom_hline(yintercept = 1,alpha=0.25,color="white")  +
  geom_hline(yintercept = max(sampleTMB, 25), alpha=0.25,color="white")  +
  
  annotate( geom="segment", x = -0.1, xend=0.1, y=10, yend=10, colour = "gray") +
  
  annotate(geom="text",y = 10,x=0,color="gray30",label="TMB-H Cutoff",  vjust = -4.5, size=2.5) +
  annotate(geom="text",y = median_tmb, x=0,color="black",label="Cohort", hjust = 0.3, vjust = 3, size=2.5) +
  annotate(geom="text",y = sampleTMB,x=0,color="red",label="This Sample",  vjust = -2.5,size=2.5) +
  
  annotate(geom="point",y = sampleTMB,x=0,color="red",shape=1, size=5) +
  annotate(geom="point",y = sampleTMB,x=0,color="red",shape=20, size=1.5) +
  
  labs(x="",y="",color="",title="",shape="",size="") +
  scale_color_manual( values= c( "gray30", "red") ) +
  scale_shape_manual(values=c(16,1)) +
  theme_classic() +
  guides(shape="none",size="none",color="none") + 
  scale_y_continuous( limits = c(0, max(sampleTMB, 25))) +
  coord_flip(clip = "off") +
  theme(
    axis.line.y = element_blank(),
    panel.grid = element_blank(), 
    text = element_text(size = 9),
    legend.title=element_blank(),
    plot.margin = unit(c(0, 12, 0, 4), "points"),
    axis.title=element_blank(),
    axis.text.y=element_blank(),
    axis.ticks.y=element_blank(),
    line = element_blank(),
    panel.background = element_rect(fill = "transparent", colour = NA),
    plot.background = element_rect(fill="transparent",color=NA)
    
  )

dev.off()