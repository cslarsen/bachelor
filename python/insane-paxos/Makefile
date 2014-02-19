check:
	pyflakes *.py

test: check
	python test.py

acceptor: check
	python acceptor.py

proposer: check
	python proposer.py

clean:
	rm -f *.pyc
