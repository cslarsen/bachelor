# For working with the ping latencies
n <- read.table("pings.txt");
m <- data.matrix(n);
summary(n);
mean(m);
rms <- function(x) sqrt(mean(x^2));
rms(m);
