# Create combined data

# Colors for mean and median
meancol <- "steelblue"
medcol <- "red"

pings_csv <- "~/bach/thesis/data/pings.csv"
pings_nf_csv <- "~/bach/thesis/data/pings-noflows.csv"
plot_pdf <- ""

args <- commandArgs(trailingOnly=TRUE)
argc <- length(args)

if ( argc >= 1 ) { pings_csv <- args[1] }
if ( argc >= 2 ) { pings_nf_csv <- args[2] }
if ( argc >= 3 ) { plot_pdf <- args[3]; pdf(plot_pdf); }

# Read data
f <- read.csv(pings_csv)
n <- read.csv(pings_nf_csv)
c <- c(f, n) # combined

# Transpose to matrix
sf <- t(summary(f$RTT))
sn <- t(summary(n$RTT))

# Add data (don't need variance, as it's the square of sd)
sf <- cbind(sf, "Std. dev"=sd(f$RTT))
sn <- cbind(sn, "Std. dev"=sd(n$RTT))

# Set names for rows
rownames(sf) <- "With flows"
rownames(sn) <- "Without flows"

# Combine them into one table
s <- rbind(sf,sn)

# Print as LaTeX
library(xtable)
print.xtable(xtable(s,
             label="table:rtt.baseline.summary",
             caption="Summary of baseline ICMP ping RTTs (ms)."),
             comment=FALSE)

# 2-by-3 plots
par(mfrow=c(3,2))

# Limits for RTT ranges
flim <- c(40, 48)#quantile(f$RTT, 0.99)) #max(f$RTT))
nlim <- c(60, 98)#quantile(f$RTT, 0.99)) #max(f$RTT))

###### With flows ######

plot(f$RTT, lwd=0.5, type="l", ylim=flim,
	 xlab="Sequence no.", ylab="RTT (ms)",
	 main="ICMP ping with flows")
abline(h=mean(f$RTT), lwd=1, col=meancol)
abline(h=median(f$RTT), lwd=1, col=medcol)

hist(f$RTT, lwd=1, breaks=length(f$RTT)/2, xlim=flim,
	 xlab="RTT (ms)",
	 main="")
abline(v=mean(f$RTT), lwd=1, col=meancol)
abline(v=median(f$RTT), lwd=1, col=medcol)

###### Without flows ######

plot(n$RTT, lwd=0.5, type="l", ylim=nlim,
     xlab="Sequence no.", ylab="RTT (ms)",
     main="ICMP ping without flows")
abline(h=mean(n$RTT), lwd=1, col=meancol)
abline(h=median(n$RTT), lwd=1, col=medcol)

hist(n$RTT, lwd=1, breaks=length(n$RTT), xlim=nlim,
	 xlab="RTT (ms)",
	 main="")
abline(v=mean(n$RTT), lwd=1, col=meancol)
abline(v=median(n$RTT), lwd=1, col=medcol)

###### Plot of both ######

clim = c(40, 98)
plot(n$RTT, ylim=clim, lwd=0.5, type="l",
     xlab="Sequence no.", ylab="RTT (ms)",
     main="ICMP ping combined")
lines(f$RTT, ylim=clim, lwd=0.5, type="l")
#
abline(h=mean(f$RTT), lwd=1, col=meancol)
abline(h=median(f$RTT), lwd=1, col=medcol)
abline(h=mean(n$RTT), lwd=1, col=meancol)
abline(h=median(n$RTT), lwd=1, col=medcol)

b <- c(n$RTT, f$RTT)
hist(b, breaks=length(b)/2, xlim=clim,
	xlab="RTT (ms)",
	main="")
#
abline(v=mean(f$RTT), lwd=1, col=meancol)
abline(v=median(f$RTT), lwd=1, col=medcol)
abline(v=mean(n$RTT), lwd=1, col=meancol)
abline(v=median(n$RTT), lwd=1, col=medcol)

