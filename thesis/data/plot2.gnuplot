set title "Plot of Latency"
set label "Time"
set ylabel "Latency (ms)"

set autoscale
set grid

# set output type and file
set term post eps
set output "data2.eps"

# Select time format
set xdata time
set timefmt "%s"
set format x "%S"
show timefmt

# input file
plot "data2.txt" using 1:2 title "Get", \
     "data2.txt" using 1:3 title "Put"
