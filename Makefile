PYTHON ?= python

.PHONY: install test lint dev

install:
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check app/ tests/ ui/

dev:
	$(PYTHON) -m app.main
