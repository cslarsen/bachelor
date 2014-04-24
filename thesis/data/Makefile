TARGETS = data1.eps data2.eps data3.eps

all: $(TARGETS)

#%.eps: %.txt
#	gnuplot plot-2series-vs-time.gnuplot

data1.eps:
	gnuplot plot-2series-vs-time.gnuplot

data2.eps:
	gnuplot plot2.gnuplot

data3.eps:
	gnuplot plot3.gnuplot

clean:
	rm -f $(TARGETS)
