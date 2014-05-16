help:
	@echo "make thesis # builds thesis"
	@echo "make repl # start python repl (use on VM)"
	@echo ""
	@echo "You should install http://csl.name/thesis/mininet-vm-x86_64.vmdk"
	@echo "and use the Makefile found on the mininet vm."
	@echo ""
	@echo "For setup instructions, see the appendix in the thesis."

# Starts a Python REPL.  Should be run on the Mininet VM.
# Can then do "import pox.core" or "import paxos.topology"
# (both should work)
repl:
	PYTHONPATH=~/pox python

.PHONY:

thesis: .PHONY
	$(MAKE) -C thesis/

