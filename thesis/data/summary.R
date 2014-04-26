# Creates summary table for inputted CSV data
# Args: <filename.csv> <table field to summarize on>
# Example: Rscript summary.R pings.csv RTT 2>/dev/null


args <- commandArgs(trailingOnly=TRUE)
file <- args[1]
data <- read.csv(args[1])
s <- summary(data[[args[2]]])
ts <- t(as.matrix(s)) # transpose summary

# Alternative: Use stargazer
# (but it's very noisy in its output)
#
#library(stargazer)
#stargazer(ts)

# Use xtable; it has less noise
library(xtable)
print.xtable(xtable(ts), include.rownames=FALSE)
