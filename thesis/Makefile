TARGETS = thesis.pdf

default: open

all: $(TARGETS)

%.pdf: %.tex
	pdflatex $< -o $@ # first pass: references -> table
	bibtex ${<:.tex=}
	pdflatex $< -o $@ # second pass: bibtex references
	pdflatex $< -o $@ # third pass: complete references

thesis.pdf: \
						theory.tex \
						thesis.tex \
	          introduction.tex \
	          thesis.bib

open: thesis.pdf
	open $<

clean:
	rm -f $(TARGETS) *.log *.toc *.aux *.bbl *.blg *.out
