.PHONY: test

test:
	.venv/bin/python3 -m pytest tests/ -v --tb=short
