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
pings_csv <- args[1]
pings_noflows_csv  <- args[2]

flows <- read.csv(pings_csv)
noflows <- read.csv(pings_noflows_csv)

# With flows, P_C = 0
Ps <- ((median(flows$RTT)-40)/2)/3
Pc <- (median(noflows$RTT) - (40+6*Ps))/6

println("\\begin{gather}")
println("  RTT_{c_0,h_9} = \\ms{40} + 6P_S + 6P_C = \\ms{",
        fnum(median(noflows$RTT)), "}")
println("  \\\\")
println("  RTT_{c_0,h_9} = \\ms{40} + 6\\cdot\\ms{",
        fnum(Ps), "} + 6P_C = \\ms{",
        fnum(median(noflows$RTT)), "}")
println("  \\\\")
println("  P_C \\approx \\ms{", fnum(Pc), "}")
println("\\end{gather}")
