f <- read.csv("pings.csv")
rf <- f$RTT

# Normal fit
pdf("pings-qqplot.pdf")
qqnorm(rf, lwd=1) #, pch=16, cex=0.5)
qqline(rf, lwd=1)
