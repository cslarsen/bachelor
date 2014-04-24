set title "Plot of ICMP Ping Latency"
set xlabel "Time (s)"
set ylabel "Latency (ms)"

set autoscale
set grid

# set output type and file
set term post eps
set output "pings.eps"

# Select time format
#set xdata time
#set timefmt "%s"
#set format x "%S"
#show timefmt

# input file
plot "pings.txt" using 1 title ""
