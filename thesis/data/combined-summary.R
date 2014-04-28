# Create combined data

f <- read.csv("pings.csv")
n <- read.csv("pings-noflows.csv")

sf <- t(summary(f$RTT))
sn <- t(summary(n$RTT))

rownames(sf) <- "With flows"
rownames(sn) <- "Without flows"

s <- rbind(sf,sn)

library(xtable)
print.xtable(xtable(s), comment=FALSE)
