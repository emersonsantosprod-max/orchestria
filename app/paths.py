"""
paths.py — resolução determinística de caminhos em dev e em builds PyInstaller.

- `db_path()`           → local gravável do SQLite (<exe_dir>/data em builds;
                          raiz do projeto em dev). Nunca depende de CWD.
- `bundled_distribuicao_xlsx()` → xlsx read-only empacotado via PyInstaller
                                  `datas=`; em dev resolve para
                                  `data/entrada/distribuicao_contratual_normalizada.xlsx`.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _exe_dir() -> Path:
    return Path(sys.executable).resolve().parent


def _bundle_root() -> Path:
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        return Path(meipass)
    return _exe_dir()


def db_path() -> Path:
    if getattr(sys, 'frozen', False):
        return _exe_dir() / 'data' / 'automacao.db'
    return _project_root() / 'data' / 'automacao.db'


def bundled_distribuicao_xlsx() -> Path:
    if getattr(sys, 'frozen', False):
        return _bundle_root() / 'data' / 'entrada' / 'distribuicao_contratual_normalizada.xlsx'
    return _project_root() / 'data' / 'entrada' / 'distribuicao_contratual_normalizada.xlsx'
