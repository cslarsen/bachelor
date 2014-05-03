all: lint check

check:
	@echo Running all unit tests
	python -u -Wall *.py
	@echo ""

lint:
	@echo Linting Python code
	pyflakes *.py || exit 0
	@echo ""

clean:
	rm -f *.pyc *.pyo
