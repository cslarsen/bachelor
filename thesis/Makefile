TARGETS = thesis.idx thesis.ind thesis.bbl thesis.pdf

# executables
PDFLATEX = pdflatex -halt-on-error
MAKEINDEX = makeindex
BIBTEX = bibtex

default: open

all: data-all $(TARGETS)

data-all:
	cd data; make all

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

sign:
	@echo "Creating signature for VM image."
	@echo "This signature can be embedded in the thesis appendix,"
	@echo "to prove that it hasn't changed after submission date."
	@echo ""
	@echo "NOTE: MAKE SURE THE PATH TO THE VM IMAGE IS CORRECT!"
	@echo ""
	@echo "(This may take a while, the file is 4 Gb!)"
	@echo ""
	gpg -a --detach-sign ~/mininet/mininet-vm-x86_64.vmdk

# Retrigger build if any of these change
thesis.tex:
	analysis.tex \
	appendix-acronyms.tex \
	appendix-mininet.tex \
	conclusion.tex \
	design.tex \
	implementation.tex \
	improvements.tex \
	introduction.tex \
	learning-switch.tex \
	openflow-versions.tex \
	packages.tex \
	paxos-algorithm.tex \
	paxos-controller.tex \
	paxos.tex \
	theory.tex

# show file on mac os x
open: data-all all
	open thesis.pdf

check: check-u8 \
			 check-dash \
			 check-label \
			 check-footnote \
			 check-em \
			 check-todo

check-u8:
	@echo '## Looking for \u8 / ALT-SHIFT-SPACE (OS X) (replace with space)'
	@grep -RI '\\xa0' *.tex || exit 0 # ignore grep's exit status
	@echo ""

check-dash:
	@echo "## Looking for single-dash hyphens (replace with double-dash)"
	@# Look for single dashes | not in commands | not in comments
	@grep -RI "[a-zA-Z]-[a-zA-Z]" *.tex \
	  | egrep -v '\.*{.*[a-zA-Z]-[a-zA-z].*}' \
	  | egrep -v '\.tex: *%' || exit 0
	@echo ""

check-label:
	@echo "## Checking for incorrect order of caption/label"
	@./grep_incorrect_labels.py `find . -name '*.tex'`
	@echo ""

check-footnote:
	@echo "## Footnotes should preferably be after punctuation"
	@grep -RI '[a-zA-Z]\\footnote' *.tex || exit 0
	@echo ""

check-em:
	@echo '## Should use \textit instead of \em'
	@grep -RI '\\em ' *.tex || exit 0
	@echo ""

check-todo:
	@echo "## To do ..."
	@grep -RI -i todo *.tex || exit 0
	@echo ""

clean:
	rm -f $(TARGETS) *.log *.toc *.aux *.bbl *.blg *.out *.ind *.ilg *.idx *.tdo *.lof *.lot *.loa *.lol
	cd data; make clean
