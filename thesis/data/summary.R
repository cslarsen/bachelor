# Creates summary table for inputted CSV data
#
# Args in order:
#    <filename.csv>
#    <table field to summarize on>
#    <caption>
#    <label>
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
xt <- xtable(ts, caption=args[3], label=args[4])
print.xtable(xt,
             comment=FALSE, # Do not print "Made by ..." comments
             include.rownames=FALSE)
