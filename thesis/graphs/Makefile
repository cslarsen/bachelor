TARGETS = client-propagation.png

all: $(TARGETS)

%.pdf: %.dot
	dot -Tpdf $< -o $@

%.eps: %.dot
	dot -Teps $< -o $@

%.png: %.dot
	dot -Tpng $< -o $@

clean:
	rm -f $(TARGETS)
