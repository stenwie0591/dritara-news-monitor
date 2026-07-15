.PHONY: setup-dev lock audit secret-check test compile docs-check check

PYTHON ?= .venv/bin/python3

setup-dev:
	$(PYTHON) -m pip install --require-hashes -r requirements-dev.lock

lock:
	$(PYTHON) -m piptools compile --allow-unsafe --generate-hashes --strip-extras -o requirements.lock requirements.txt
	$(PYTHON) -m piptools compile --allow-unsafe --generate-hashes --strip-extras -o requirements-dev.lock requirements-dev.txt

audit:
	$(PYTHON) -m pip_audit -r requirements.lock --require-hashes
	$(PYTHON) -m pip check

secret-check:
	$(PYTHON) -m scripts.check_secret_hygiene

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

compile:
	$(PYTHON) -m compileall -q main.py src migrations tests

docs-check:
	$(PYTHON) scripts/check_docs.py

check: compile docs-check secret-check test
