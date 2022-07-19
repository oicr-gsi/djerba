

#MSI median
args = commandArgs(trailingOnly=TRUE)
file <- args[1]

sample_boot <- read.table(file)

print(quantile(sample_boot$V4))

