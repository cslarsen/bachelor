# Script for trying to plot gamma distribution of pings
# Here we read the ping RTT data and try to plot
# as a gamma distribution and as a histogram.
# You may want to play with the qquant parameter.
# Ideally, if we get the right distribution, you should see that the
# histogram and curve plot should look alike.

args <- commandArgs(trailingOnly = TRUE)

# Output plot to EPS file
infile <- args[1]
outfile <- args[2]

cat("Reading from", infile, "\n")
cat("Writing to", outfile, "\n")

# Output file
pdf(outfile)

# Input file
raw <- read.table(infile)
m <- data.matrix(raw)

summary(m)

# Estimate shape and scale for gamma distribution
# quantile_at is typically 0.95 (don't really know what it is)
# (maybe it's the cutoff percent on the frequency of values at which
#  we want to estimate, or say that we want to cover 95%, e.g., of the
#  samples, or something)
estgamma <- function(values, quantile_at) {
	myfun <- function(shape, quantile_at, values) {
		scale <- mean(values) / shape
  		pgamma(quantile(values, quantile_at), shape, scale=scale) - quantile_at
  	}

	callfun <- function(shape) {
  		myfun(shape, quantile_at, values)
	}

	# If uniroot fails, then upper must be increased,
	# upper must be so large that funfun gives a negative
	# value (could be automated)
	tmp <- uniroot(callfun, lower=-10^9, upper=10^9)
	myshape <- tmp$root
	
	myscale <- median(m)/tmp$root
	# NOTE: Using median(m) gives better results!
	#(because it ignores outliers) (but it was originally mean)
	c(myshape, myscale)
}

qquant <- 0.97
est <- estgamma(m, qquant)
myshape <- est[1]
myscale <- est[2]

qq <- qgamma(qquant, shape=myshape, scale=myscale)
  integrate(function(x) x*dgamma(x,shape=myshape, scale=myscale),
      lower=0, upper=Inf)

# Plot with given shape and scale (for gamma) and
# number of points on plot
plotit <- function(shape, scale, numpoints, left, right) {
	x <- seq(left, right, length=numpoints)
    y <- dgamma(x, shape=shape, scale=scale)
    plot(x,y,type="l",lwd=1,col="red",ylab="dgamma",main=sprintf("Gamma shape=%f scale=%f quant=%.2f", shape, scale, qquant),xlab="RTT/2 (ms)")
}

# plotting left and right points (x-axis)
left <- 40#min(m) # 40=min expected RTT
right <- max(m)

par(mfrow=c(2,1)) # two rows, 1 column
plotit(myshape, myscale, length(m), left=left, right=right)
abline(v=mean(m), col="gray", lwd=2)
abline(v=median(m), col="blue", lwd=2)

# Expected known RTT 40 ms
abline(v=40, col="green", lwd=2)

hist(m, xlim=c(left, right), lwd=1, breaks=length(m), xlab="RTT/2 (ms)", main="Ping RTT/2 Histogram")
# Show mean as a vertical line (v=...)
abline(v=mean(m), col="gray", lwd=2)
abline(v=median(m), col="blue", lwd=2)

# Expected known RTT 40 ms
abline(v=40, col="green", lwd=2)

# TODO: Try to use the normal distribution...

# turn off plot destination
dev.off()
