# Script for trying to plot gamma distribution of pings
# Here we read the ping latency data (RTT/2) and try to plot
# as a gamma distribution and as a histogram.
# You may want to play with the qquant parameter.
# Ideally, if we get the right distribution, you should see that the
# histogram and curve plot should look alike.

raw <- read.table("~/bach/thesis/data/pings.txt")
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
	tmp <- uniroot(callfun, lower=min(m), upper=1000000)
	myshape <- tmp$root
	myscale <- mean(m)/tmp$root
	c(myshape, myscale)
}

qquant <- 0.999
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
    plot(x,y,type="l",lwd=2,col="red")
}

par(mfrow=c(2,1)) # two rows, 1 column
plotit(myshape, myscale, 200, left=min(m), right=max(m))
hist(m, xlim=c(min(m), max(m)))
