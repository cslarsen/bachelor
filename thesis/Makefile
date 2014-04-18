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
	analysis.tex \
	appendix-acronyms.tex \
	appendix-mininet.tex \
	conclusion.tex \
	introduction.tex \
	openflow-versions.tex \
	openflow.tex \
	packages.tex \
	paxos-algorithm.tex \
	paxos-controller.tex \
	paxos.tex \
	theory.tex

# show file on mac os x
open: thesis.pdf
	open $<

check:
	@echo "Searching for some common errors in LaTeX"
	@echo ""
	@echo "--------------------------------------------------------------"
	@echo "Looking for \\u8 / ALT-SHIFT-SPACE (OS X) (replace with space)"
	@echo "--------------------------------------------------------------"
	@grep -RI '\\xa0' *.tex || exit 0 # ignore grep's exit status
	@echo ""
	@echo "----------------------------------------------------------"
	@echo "Looking for single-dash hyphens (replace with double-dash)"
	@echo "----------------------------------------------------------"
	@# Look for single dashes | not in commands | not in comments
	@grep -RI "[a-zA-Z]-[a-zA-Z]" *.tex \
	  | egrep -v '\.*{.*[a-zA-Z]-[a-zA-z].*}' \
	  | egrep -v '\.tex: *%' || exit 0
	@echo ""
	@echo "-----"
	@echo "TODOs"
	@echo "-----"
	@grep -RI -i todo *.tex
	@echo ""

clean:
	rm -f $(TARGETS) *.log *.toc *.aux *.bbl *.blg *.out *.ind *.ilg *.idx *.tdo *.lof *.lot *.loa
