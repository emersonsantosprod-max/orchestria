"""
paths.py — resolução determinística de caminhos em dev e em builds PyInstaller.

- `db_path()`           → local gravável do SQLite (<exe_dir>/data em builds;
                          raiz do projeto em dev). Nunca depende de CWD.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


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


def saida_dir() -> Path:
    root = _exe_dir() if getattr(sys, 'frozen', False) else _project_root()
    return root / 'data' / 'saida'


def logs_dir() -> Path:
    root = _exe_dir() if getattr(sys, 'frozen', False) else _project_root()
    return root / 'logs'


def ui_dist_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return _bundle_root() / 'app' / 'ui' / 'web' / 'dist'
    return _project_root() / 'app' / 'ui' / 'web' / 'dist'
