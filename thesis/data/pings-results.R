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

println("")
println("\\begin{gather*}")
println("  RTT_{c_0,h_9} = 40~ms + 2L = ", fnum(median(rtt)), "~ms \\\\")
println("  L = \\sum P_S + \\sum P_C = ", fnum(L), "~ms \\\\")
println("  \\text{but}~P_C \\to 0~\\text{when all the flows are installed, so} \\\\")
println("  \\sum P_S = P_{S_1} + P_{S_2} + P_{S_3} = 3P_S = ", fnum(L), "~ms \\\\")
println("  P_S \\approx ", fnum(Ps), "~ms")
println("  \\label{", args[3], "}")
println("\\end{gather*}")
println("")
println("In other words, the one--way latency per switch is somewhere around $", fnum(Ps), "~ms$.")
println("")
