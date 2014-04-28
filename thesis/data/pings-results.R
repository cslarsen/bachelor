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
Ps <- (median(rtt)-40)/6

println("\\begin{align}")
println("  RTT_{c_0,h_9} &= \\ms{40} + 2\\sum_n^3 P_{S_n} ",
        "+ 2\\sum_n^3 P_{C_n} \\\\")
println("   &= \\ms{40} + 6P_S + 6P_C")
println("\\end{align}")

println("but $P_C\\to\\ms{0}$ when all the flows are installed and each switch")
println("do the same processing ($P_{S_1} = P_{S_2} = P_{S_3}$) so")

println("\\begin{align}")
println("  6P_S &= RTT_{c_0,h_9} - \\ms{40} - \\ms{0} \\\\")
println("       &= \\ms{", fnum(median(rtt)), "} - \\ms{40} \\\\")
println("       &= \\ms{", fnum(median(rtt)-40), "} \\\\")
println("  P_S &\\approx \\ms{", fnum((median(rtt)-40)/6), "}")
println("  \\label{", args[3], "}")
println("\\end{align}")

println("")
println("In other words, the one--way latency per switch is ",
        "somewhere around $\\ms{", fnum(Ps), "}$.")
