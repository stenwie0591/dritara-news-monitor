.PHONY: setup-dev test compile docs-check check

PYTHON ?= .venv/bin/python3

setup-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

compile:
	$(PYTHON) -m compileall -q main.py src tests

docs-check:
	$(PYTHON) scripts/check_docs.py

check: compile docs-check test
