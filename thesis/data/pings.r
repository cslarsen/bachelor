# For working with the ping latencies

file <- "pings.txt"

println <- function(fmt="", ...) {
  cat(sprintf(fmt, ...), "\n", sep="")
}

println("Reading ping-data from %s", file)
n <- read.table("pings.txt")
m <- data.matrix(n)

println("Summary of ping data")
summary(n)

println()
println("Mean: %f", mean(m))

rms <- function(x) sqrt(mean(x^2))
println("RMS: %f", rms(m))

# Percent of pings larger than x
pover <- function(x) 100*(1-pnorm(x, mean=mean(m), sd=sd(m)))

println()
println("Min value: %f", min(m))
println("Assuming a normal distribution:")
println("%f%% of the pings are larger than %f", pover(min(m)), min(m))

# I don't think these are normally distributed,
# (e.g., if you calc pover for some values, it doesn't make sense when
# compared to quantiles)

# So lets' try a gamma distribution based on
# http://stackoverflow.com/questions/14266354/how-can-i-estimate-the-shape-and-scale-of-a-gamma-dist-with-a-particular-mean-a

myfun <- function(shape, quantile_at, vals) {
  scale <- mean(vals) / shape
  pgamma(quantile(vals, quantile_at), shape, scale=scale) - quantile_at
}

qquant <- 0.95

funfun <- function(shape) {
  myfun(shape, qquant, m)
}

tmp <- uniroot(funfun, lower=min(m), upper=1000000)
myshape <- tmp$root
myscale <- mean(m)/tmp$root

qq <- qgamma(qquant, shape=myshape, scale=myscale)
  integrate(function(x) x*dgamma(x,shape=myshape, scale=myscale),
      lower=0, upper=Inf)
cat("qq:", qq," for qquant =", qquant*100, "%\n")
println("Myshape %f", myshape)
println("Myscale %f", myscale)
plot(m)
