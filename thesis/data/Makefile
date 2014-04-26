TARGETS = data1.eps data2.eps data3.eps pings.pdf pings-summary.tex

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
	Rscript summary.R $< RTT \
		"Summary of ICMP ping RTTs" \
		"table:baseline.summary" > $@

pings.txt:
	scp mininet:~/pings.txt $@

# Dowload data from mininet
update:
	scp mininet:~/pings.txt mininet:~/pings-noflows.txt . || exit 0

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
	make bench-baseline bench-baseline-noflows

clean:
	rm -f $(TARGETS) *.pyc Rplots.pdf ping-plot.pdf NA
