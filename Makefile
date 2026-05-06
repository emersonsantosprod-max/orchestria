PYTHON ?= python

.PHONY: install test lint dev build-win clean distclean quality-gate quality-gate-update

install:
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check app/ tests/ ui/

dev:
	$(PYTHON) -m app.main

quality-gate:
	$(PYTHON) -m scripts.quality_gate

quality-gate-update:
	$(PYTHON) -m scripts.quality_gate --update-baseline

build-win:
	./venv_win/Scripts/pyinstaller.exe --clean --noconfirm AutomacaoMedicao.spec

clean:
	rm -rf .pytest_cache .ruff_cache *.egg-info logs baseline
	find . -type d -name __pycache__ -not -path './venv*' -not -path './venv_win*' -exec rm -rf {} +

distclean: clean
	rm -rf build dist
