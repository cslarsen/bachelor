TARGETS = thesis.pdf

PDFLATEX = pdflatex -halt-on-error
MAKEINDEX = makeindex
BIBTEX = bibtex

default: open

all: $(TARGETS)

%.pdf: %.tex
	$(PDFLATEX) $< -o $@ # first pass: references -> table
	$(MAKEINDEX) ${<:.tex=}
	$(BIBTEX) ${<:.tex=}
	$(PDFLATEX) $< -o $@ # second pass: bibtex references
	$(PDFLATEX) $< -o $@ # third pass: complete references

%.ind: %.idx
	makeindex %< -o $@

thesis.pdf: \
						theory.tex \
						thesis.tex \
	          introduction.tex \
	          thesis.bib

open: thesis.pdf
	open $<

clean:
	rm -f $(TARGETS) *.log *.toc *.aux *.bbl *.blg *.out *.ind *.ilg *.idx
