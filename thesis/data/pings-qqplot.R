f <- read.csv("pings.csv")
rf <- f$RTT

f <- read.csv("~/bach/thesis/data/pings.csv")
rf <- f$RTT

n <- read.csv("~/bach/thesis/data/pings-noflows.csv")
nf <- n$RTT

# Normal fit
pdf("~/bach/thesis/data/pings-qqplot.pdf")

par(mfrow=c(1,2))

qqnorm(rf, lwd=1,
       main="Normal Q-Q Plot (with flows)")
       #pch=16, cex=0.5
qqline(rf, lwd=2, col="red")

qqnorm(nf, lwd=1,
       main="Normal Q-Q Plot (without flows)")
       #pch=16, cex=0.5
qqline(nf, lwd=2, col="red")
