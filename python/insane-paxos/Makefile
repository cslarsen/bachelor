PYFLAGS = -Wall -u
PYTHON = python $(PYFLAGS)
PYFLAKES = pyflakes

config: check
	$(PYTHON) config.py

check:
	$(PYFLAKES) *.py

test: check
	$(PYTHON) test.py

acceptor: check
	$(PYTHON) acceptor.py

proposer: check
	$(PYTHON) proposer.py

clean:
	rm -f *.pyc
