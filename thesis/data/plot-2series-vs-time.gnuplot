set title "Plot of RTT"
set label "Time (s)"
set ylabel "RTT (ms)"

set autoscale
set grid

# set output type and file
set term post eps
set output "data1.eps"

# Select time format
set xdata time
set timefmt "%s"
set format x "%S"
show timefmt

# input file
plot "data1.txt" using 1:2 title "Get", \
     "data1.txt" using 1:3 title "Put"
