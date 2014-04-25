TARGETS = data1.eps data2.eps data3.eps pings.eps

all: $(TARGETS)

#%.eps: %.txt
#	gnuplot plot-2series-vs-time.gnuplot

data1.eps:
	gnuplot plot-2series-vs-time.gnuplot

data2.eps:
	gnuplot plot2.gnuplot

data3.eps:
	gnuplot plot3.gnuplot

pings.eps:
	gnuplot plot-ping.gnuplot

r:
	Rscript pings.R

%.pdf: %.R
	Rscript $< $@

ping-graph.pdf: ping-graph.R
	Rscript $< pings.txt $@

bench-baseline:
	@echo Will run bench-baseline on mininet vm,
	@echo fetch results and regenerate graphs and key figures.
	ssh mininet make bench-baseline
	ssh mininet "cat ~/pings.txt" | \
		grep time= | cut -f4 -d= | cut -f1 -d' ' > pings.txt
	wc -l pings.txt
	gnuplot plot-ping.gnuplot
	#Rscript ping-graph.R pings.txt

benchmarks:
	@echo Running ALL benchmarks, this may take A WHILE ...
	make bench-baseline

clean:
	rm -f $(TARGETS) *.pyc Rplots.pdf ping-plot.pdf NA
