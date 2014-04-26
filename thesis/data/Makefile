TARGETS = data1.eps data2.eps data3.eps pings.pdf

all: $(TARGETS)

.PHONY:

data1.eps:
	gnuplot plot-2series-vs-time.gnuplot

data2.eps:
	gnuplot plot2.gnuplot

data3.eps:
	gnuplot plot3.gnuplot

pings.pdf: pings.csv
	Rscript bench-baseline.R $< $@

pings-noflows.pdf: pings-noflows.csv
	Rscript bench-baseline.R $< $@

r:
	Rscript pings.R

%.pdf: %.R
	Rscript $< $@

ping-graph.pdf: ping-graph.R
	Rscript $< pings.txt $@

pings-summary.tex: pings.csv
	Rscript summary.R $< RTT 2>/dev/null | grep -v '^%' | grep -v '^$$' > $@

pings.txt: .PHONY
	scp mininet:~/pings.txt $@

pings-noflows.txt: .PHONY
	scp mininet:~/pings-noflows.txt $@

pings.csv: pings.txt
	python -c "import tools; tools.pings2csv('"$<"')" > $@

pings-noflows.csv: pings-noflows.txt
	python -c "import tools; tools.pings2csv('"$<"')" > $@

bench-baseline:
	@echo Will run bench-baseline on mininet vm,
	@echo fetch results and regenerate graphs and key figures.
	@echo ""
	ssh mininet make bench-baseline
	make pings.pdf

bench-baseline-noflows:
	ssh mininet make bench-baseline-noflows
	make pings-noflows.pdf

benchmarks:
	@echo Running ALL benchmarks, this may take A WHILE ...
	make bench-baseline

clean:
	rm -f $(TARGETS) *.pyc Rplots.pdf ping-plot.pdf NA
