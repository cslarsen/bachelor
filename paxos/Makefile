check:
	# Lint all Python files
	pyflakes `find . -name '*.py' | grep -v __init__.py`

repl:
	PYTHONPATH=~/pox python

clean:
	# Remove all .pyc and .pyo files
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	rm -rf __pycache__
