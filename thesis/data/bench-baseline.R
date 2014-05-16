println <- function(...) {
	cat(..., "\n", sep="")
}

print_table <- function(label, caption, data) {
	println("\\begin{table}")
	println("  \\caption{", caption, "}")
	println("  \\label{", label, "}")
	println("\\end{table}")
}

args <- commandArgs(trailingOnly = TRUE)

infile <- "pings.csv"
outfile <- ""

if ( length(args) >= 2 ) {
	infile <- args[1]
	outfile <- args[2]
}

println("Reading ICMP PING RTT data from ", infile)
pings <- read.csv(infile)
summary(pings)

plotSlice <- function(x, y, left, right, xlab="x", ylab="y", type="l",...) {
	x <- x[left:right]
	y <- y[left:right]
	plot(x,
	     y,
	     xlim=c(left, right),
	     ylim=c(min(y), max(y)),
	     xlab=xlab,
	     ylab=ylab,
	     type=type,
	     ...)
}

print_table("table:bench.baseline.summary",
            "Summary of baseline benchmark",
            pings)

if ( length(outfile) > 0 ) {
	println("Writing plots to ", outfile)
	pdf(outfile)
}

# Graphs on top of each other
#par(mfrow=c(3,1))
par(mfrow=c(2,1))

left <- 1
#split <- 30
split <- left

#plotSlice(pings$Req,
#			 pings$RTT,
#			 left=left,
#			 right=split,
#          xlab="ICMP request no.",
#          ylab="RTT (ms)",
#          main="RTT during ramp-up",
#          lwd=1, type="l")

plotSlice(pings$Req,
			 pings$RTT,
			 left=split,
			 right=length(pings$RTT),
          xlab="ICMP req no",
          ylab="RTT (ms)",
          main="ICMP ping RTT L2 learning switch with flows",
          lwd=1, type="l")
# Mark mean and median
abline(h=mean(pings$RTT), col="gray")
abline(h=median(pings$RTT), col="red")

rtt <- pings$RTT
#qdelta = 0.05
#xlim = c(quantile(rtt, qdelta), quantile(rtt, 1-qdelta))
xlim = c(40, quantile(rtt, 0.995))#max(rtt))
hist(rtt, lwd=1, breaks=length(rtt)/10, xlab="RTT (ms)",
    xlim=xlim,
    main="Histogram RTT (excerpt)")

# Add mean and median
abline(v=mean(rtt), col="gray")
abline(v=median(rtt), col="red")

#summary(pings$RTT)
