# ALl warnings on, unbuffered stdio
PYFLAGS = -Wall -u

help:
	@echo "Start server first with: python server.py"
	@echo "Then run client with: python client.py"

server: check
	python $(PYFLAGS) server.py

client: check
	python $(PYFLAGS) client.py

check:
	pyflakes *.py

clean:
	rm -f *.pyc
