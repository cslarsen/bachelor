# Create combined data

# Read data
f <- read.csv("pings.csv")
n <- read.csv("pings-noflows.csv")

# Transpose to matrix
sf <- t(summary(f$RTT))
sn <- t(summary(n$RTT))

# Add data
sf <- cbind(sf, "Std.dev"=sd(f$RTT), "Var"=var(f$RTT))
sn <- cbind(sn, "Std.dev"=sd(n$RTT), "Var"=var(n$RTT))

# Set names for rows
rownames(sf) <- "With flows"
rownames(sn) <- "Without flows"

# Combine them into one table
s <- rbind(sf,sn)

# Print as LaTeX
library(xtable)
print.xtable(xtable(s,
             label="table:rtt.baseline.summary",
             caption="Summary of baseline ICMP ping RTTs (ms)"),
             comment=FALSE)
