TARGETS = topo1.pdf topo2.pdf

all: $(TARGETS)

view1: topo1.png
	open topo1.png

view2: topo2.png
	open topo2.png

%.png: %.dot
	dot -Tpng $< -o $@

%.pdf: %.dot
	dot -Tpdf $< -o $@

clean:
	rm -f $(TARGETS) *.png *.pdf
