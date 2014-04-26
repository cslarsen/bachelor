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

infile <- "~/bach/thesis/data/pings.csv"
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
par(mfrow=c(3,1))

left <- 1
split <- 30

plotSlice(pings$Req,
			 pings$RTT,
			 left=left,
			 right=split,
          xlab="ICMP request no.",
          ylab="RTT (ms)",
          main="RTT during ramp-up",
          lwd=1, type="l", pch=20)

plotSlice(pings$Req,
			 pings$RTT,
			 left=split,
			 right=length(pings$RTT),
          xlab="ICMP request no.",
          ylab="RTT (ms)",
          main="RTT after ramp-up",
          lwd=1, type="l", pch=20)
# Mark mean and median
abline(h=mean(pings$RTT), col="gray")
abline(h=median(pings$RTT), col="red")

rtt <- pings$RTT
qdelta = 0.05
xlim = c(quantile(rtt, qdelta), quantile(rtt, 1-qdelta))
hist(rtt, lwd=1, breaks=length(rtt), xlab="RTT (ms)",
    xlim=xlim,
    main="Histogram RTT")

# Add mean and median
abline(v=median(rtt), col="red")
abline(v=mean(rtt), col="gray")

#summary(pings$RTT)
