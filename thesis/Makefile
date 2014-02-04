TARGETS = thesis.idx thesis.ind thesis.bbl thesis.pdf

# executables
PDFLATEX = pdflatex -halt-on-error
MAKEINDEX = makeindex
BIBTEX = bibtex

default: open

all: $(TARGETS)

# first parse
%.aux %.idx %.log %.out %.toc: %.tex
	$(PDFLATEX) $<

# index
%.ilg %.ind: %.idx
	$(MAKEINDEX) ${<:.idx=}

# bibliography
%.bbl %.blg: %.aux
	$(BIBTEX) ${<:.aux=}

# two passes to resolve links
%.pdf: %.tex %.ind %.bbl
	$(PDFLATEX) $< -o $@
	$(PDFLATEX) $< -o $@

# included files in thesis.tex
thesis.tex: \
	appendix-acronyms.tex \
	appendix-mininet.tex \
	conclusion.tex \
	extending-openflow.tex \
	introduction.tex \
	paxos-controller.tex \
	paxos-switch.tex \
	theory.tex

# show file on mac os x
open: thesis.pdf
	open $<

clean:
	rm -f $(TARGETS) *.log *.toc *.aux *.bbl *.blg *.out *.ind *.ilg *.idx *.tdo
