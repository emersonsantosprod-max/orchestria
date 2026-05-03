"""
connection.py — responsabilidade única: abrir conexão SQLite.

Não cria schema. Não popula. Não toma decisões.
Composition root chama create_schema() separadamente, uma vez.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from app.infrastructure.paths import db_path

logger = logging.getLogger(__name__)


def conectar(path: Path | str | None = None) -> sqlite3.Connection:
    """Abre conexão no caminho canônico.

    `path` pode ser sobrescrito em testes (tmp_path ou ':memory:').
    WAL + busy_timeout garantem que travas de runs anteriores viram
    OperationalError dentro de ~5s — recuperável pela API.
    """
    resolved = path if path is not None else db_path()
    logger.debug("db.conectar: %s", resolved)

    if str(resolved) != ":memory:":
        Path(resolved).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(resolved), timeout=5)
    conn.row_factory = sqlite3.Row

    if str(resolved) != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL")

    conn.execute("PRAGMA busy_timeout=5000")
    return conn
