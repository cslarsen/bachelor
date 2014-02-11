TARGETS = proposer.png

check:
	python paxos1.py

all: $(TARGETS)

%.png: %.dot
	dot -Tpng $< -o $@

clean:
	rm -f $(TARGETS)
