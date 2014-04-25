println <- function(...) {
	cat(..., "\n", sep="")
}

print_table <- function(label, caption, data) {
	println("\\begin{table}")
	println("  \\caption{", caption, "}")
	println("  \\label{", label, "}")
	println("\\end{table}")
}

pings <- read.csv("~/bach/thesis/data/pings.csv")
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
        
# Two graphs on top of each other
par(mfrow=c(2,1))
plotSlice(pings$Req, pings$RTT, 1, 19,
          xlab="ICMP request no.",
          ylab="RTT (ms)",
          main="RTT during ramp-up")
plotSlice(pings$Req, pings$RTT, 20, length(pings$RTT),
          xlab="ICMP request no.",
          ylab="RTT (ms)",
          main="RTT after ramp-up")

#quantile(pings$RTT, 0.25)