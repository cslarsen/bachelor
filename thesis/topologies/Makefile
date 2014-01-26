TARGETS = sdn-paxos.eps

all: $(TARGETS)

%.eps: %.dot
	dot -Teps $< > $@

%.png: %.dot
	dot -Tpng $< > $@
	open $@

clean:
	rm -f $(TARGETS) *.png *.pdf
