"""
paths.py — resolução determinística de caminhos em dev e em builds PyInstaller.

- `db_path()`             → local gravável do SQLite (<exe_dir>/data em
                            builds; raiz do projeto em dev). Nunca depende
                            de CWD.
- `exports_dir()`         → diretório de exports (xlsx processados,
                            relatórios txt). Garante existência do dir.
- `processed_output_path` → xlsx processado por feature, em `exports_dir`.
"""

from __future__ import annotations

import os
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


def exports_dir() -> Path:
    path = db_path().parent / 'exports'
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed_output_path(feature: str) -> Path:
    path = exports_dir() / f'medicao_{feature}_processada.xlsx'
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    root = _exe_dir() if getattr(sys, 'frozen', False) else _project_root()
    return root / 'logs'


def validar_arquivo_referenciado(
    path: str | Path,
    exts: tuple[str, ...] = ('.xlsx', '.xls'),
) -> Path:
    """Valida que `path` é arquivo existente, com extensão suportada e legível.

    Fonte canônica de validação de path para registry e Execute. Levanta
    FileNotFoundError, ValueError ou PermissionError com mensagens claras.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f'Arquivo não encontrado: {path}')
    if p.suffix.lower() not in exts:
        raise ValueError(
            f'Extensão não suportada: {p.suffix} (esperado: {", ".join(exts)})'
        )
    if not os.access(p, os.R_OK):
        raise PermissionError(f'Sem permissão de leitura: {path}')
    return p


def ui_dist_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return _bundle_root() / 'app' / 'ui' / 'web' / 'dist'
    return _project_root() / 'app' / 'ui' / 'web' / 'dist'
