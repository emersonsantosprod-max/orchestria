PYTHON ?= python

.PHONY: install test lint dev build-win

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
