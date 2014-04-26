flows <- read.csv("~/bach/thesis/data/pings.csv")
noflows <- read.csv("~/bach/thesis/data/pings-noflows.csv")

rttf <- flows$RTT
rttn <- noflows$RTT

reqf <- flows$Req
reqn <- noflows$Req

both <- c(rttf, rttn)

ylim = c(min(both), max(both))
xlim = c(min(reqf, reqn), max(reqf, reqn))

# two plots
par(mfrow=c(2,1))

plot(rttf, type="l", lwd=1, xlab="ICMP req no", ylab="RTT (ms)",
		main="Ping RTTs for L2 learning switch",
		ylim=ylim, xlim=xlim)
lines(rttn, lwd=1, ylim=ylim, xlim=xlim)

# means
abline(h=mean(rttf), lwd=1, col="gray")
abline(h=mean(rttn), lwd=1, col="gray")
# medians
abline(h=median(rttf), lwd=1, col="red")
abline(h=median(rttn), lwd=1, col="red")

xlim <- c(min(both), quantile(both, 0.99))#max(both))
hist(both, lwd=1, breaks=length(both)/10,
     main="Histogram of ICMP ping for L2 learning switch",
		xlab="RTT (ms)",
		xlim=xlim)
# means
abline(v=mean(rttf), lwd=1, col="gray")
abline(v=mean(rttn), lwd=1, col="gray")
# medians
abline(v=median(rttf), lwd=1, col="red")
abline(v=median(rttn), lwd=1, col="red")
