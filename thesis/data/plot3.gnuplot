set title "Plot of RTT"
set label "Time"
set ylabel "RTT (ms)"

set autoscale
set grid

# set output type and file
set term post eps
set output "data3.eps"

# Select time format
set xdata time
set timefmt "%s"
set format x "%S"
show timefmt

# input file
plot "data3.txt" using 1:2 title "Get", \
     "data3.txt" using 1:3 title "Put"
