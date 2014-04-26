args <- commandArgs(trailingOnly=TRUE)

flows_csv <- "~/bach/thesis/data/pings.csv"
noflows_csv <- "~/bach/thesis/data/pings-noflows.csv"

if ( length(args) >= 2 ) {
	flows_csv <<- args[1]
	noflows_csv <<- args[2]
}

if ( length(args) >= 3 ) {
	pdf(args[3])
}

flows <- read.csv(flows_csv)
noflows <- read.csv(noflows_csv)

rttf <- flows$RTT
rttn <- noflows$RTT

reqf <- flows$Req
reqn <- noflows$Req

both <- c(rttf, rttn)

ylim = c(min(both), quantile(both, 0.995))#max(both))
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

xlim <- c(min(both), quantile(both, 0.995))#max(both))
hist(both, lwd=1, breaks=length(both),
     main="Histogram of ICMP ping for L2 learning switch",
		xlab="RTT (ms)",
		xlim=xlim)
# means
abline(v=mean(rttf), lwd=1, col="gray")
abline(v=mean(rttn), lwd=1, col="gray")
# medians
abline(v=median(rttf), lwd=1, col="red")
abline(v=median(rttn), lwd=1, col="red")
