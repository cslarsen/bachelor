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

# See equation in thesis (P_S + P_C)
L <- (median(rtt) - 40)/2
Ps <- L/3

println("")
println("\\begin{gather}")
println("  RTT_{c_0,h_9} = \\ms{40} + 2\\sum_n^3 P_{S_n} + 2\\sum_n^3 P_{C_n} = \\ms{", fnum(median(rtt)), "}")
println("\\end{gather}")
println("but $P_C\\to0$ when all the flows are installed and each switch")
println("do the same processing ($P_{S_1} = P_{S_2} = P_{S_3}$) so")
println("\\begin{gather}")
println("  3P_S = \\ms{", fnum(L), "} \\\\")
println("  P_S \\approx \\ms{", fnum(Ps), "}")
println("  \\label{", args[3], "}")
println("\\end{gather}")
println("")
println("In other words, the one--way latency per switch is somewhere around $\\ms{", fnum(Ps), "}$.")
println("")
