TARGETS = thesis.idx thesis.ind thesis.bbl thesis.pdf

# executables
PDFLATEX = pdflatex -halt-on-error
MAKEINDEX = makeindex
BIBTEX = bibtex

# other makefiles
DATA_DIR = data

VMFILE = "/Users/csl/VirtualBox VMs/Mininet Clone 2014-04-29 w_new Open vSwitch/Mininet Clone 2014-04-29 w/new Open vSwitch-disk1.vmdk"

# List all targets that are not actual files
.PHONY: data-all all default benchmarks full sign open check

default: open

all: data-all $(TARGETS)

data-all:
	$(MAKE) -C $(DATA_DIR) all

benchmarks:
	@echo '# Running ALL simulations and benchmarks'
	@echo '# ... this may take A WHILE!'
	$(MAKE) -C $(DATA_DIR) benchmarks

# Run simulations/benchmarks, generate plots and key figures, then generate
# thesis.  TODO: Automatically generate commentary, observations and
# conclusions (naah)
#
# The only thing missing is generating the signature (make sign),
# because it requires passphrase user input
#
full: benchmarks all

# first parse
%.aux %.idx %.log %.out %.toc: %.tex
	$(PDFLATEX) $<

# index
%.ilg %.ind: %.idx
	#$(MAKEINDEX) ${<:.idx=}
	# Not needed with imakeidx package in TeX Live

# bibliography
%.bbl %.blg: %.aux
	$(BIBTEX) ${<:.aux=}

# two passes to resolve links
%.pdf: %.tex %.ind %.bbl
	$(PDFLATEX) $< -o $@
	$(PDFLATEX) $< -o $@

mininet-vm-x86_64.vmdk.asc:
	@echo "# Creating signature for VM image."
	@echo "# This signature can be embedded in the thesis appendix,"
	@echo "# to prove that it hasn't changed after submission date."
	@echo "# (This may take a while -- around 40-50 secs)"
	time gpg -a --output=$@ --detach-sign $(VMFILE)

sign: mininet-vm-x86_64.vmdk.asc

# Retrigger build if any of these change
thesis.tex:
	abstract.tex \
	acronyms.tex \
	acknowledgments.tex \
	analysis.tex \
	appendix-mininet.tex \
	colophon.tex \
	compiling.tex \
	conclusion.tex \
	design-openflow.tex \
	design-paxos.tex \
	design-topology.tex \
	design.tex \
	impl-flows.tex \
	implementation.tex \
	improvements.tex \
	introduction.tex \
	learning-switch.tex \
	paxos-algorithm.tex \
	paxos-controller.tex \
	preamble.tex \
	results.tex \
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
	@echo "## Looking for double-dash hyphens (replace with single dash)"
	@egrep -RI '[^- ]--[a-zA-Z]' *.tex || exit 0
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
	rm -f $(TARGETS) *.log *.toc *.aux *.bbl *.blg *.out *.ind *.ilg *.idx *.tdo *.lof *.lot *.loa *.lol #mininet-vm-x86_64.vmdk.asc
	$(MAKE) -C $(DATA_DIR) clean
