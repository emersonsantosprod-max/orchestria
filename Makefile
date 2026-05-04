PYTHON ?= python

.PHONY: install test lint dev build-win clean distclean

install:
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check app/ tests/ ui/

dev:
	$(PYTHON) -m app.main

build-win:
	venv_win\Scripts\pyinstaller.exe --clean --noconfirm AutomacaoMedicao.spec

clean:
	rm -rf .pytest_cache .ruff_cache *.egg-info logs baseline
	find . -type d -name __pycache__ -not -path './venv*' -not -path './venv_win*' -exec rm -rf {} +

distclean: clean
	rm -rf build dist
