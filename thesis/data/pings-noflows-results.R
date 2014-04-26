# Creates result TeX file for ping RTT
#
# Args in order:
#    <filename.csv>
#    <table field to summarize on>
#    <label>

println <- function(...) {
  cat(..., "\n", sep="")
}

# Format float with 2 decimals
fnum <- function(n) {
  sprintf("%.2f", n)
}

args <- commandArgs(trailingOnly=TRUE)
file <- args[1]
data <- read.csv(args[1])

rtt <- data[[args[2]]]

# See equation in thesis
L <- (median(rtt) - 40)/2
Ps <- L/3

# TODO: Read result from pings-results run (do the run here)
#       do get value of Ps, then plug that in to get the value of
#       P_C
# TODO: Make new equation
