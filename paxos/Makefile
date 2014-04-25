check:
	# Lint all Python files
	find . -name '*.py' -exec pyflakes {} \;

pox:
	# Start POX controller
	cd ~/pox; ./pox.py log.level --DEBUG paxos

mininet:
	# Start mininet
	sudo mn --topo single,3 --switch ovsk --controller remote

repl:
	PYTHONPATH=~/pox python

clean:
	# Remove all .pyc and .pyo files
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	rm -rf __pycache__
