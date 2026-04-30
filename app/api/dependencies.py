"""
dependencies.py — injeção de dependência para FastAPI.

Cada request recebe sua própria conexão SQLite.
A conexão é fechada automaticamente ao fim do request (finally do generator).

Uso nas rotas:

    from app.api.dependencies import get_conn
    from app.infrastructure.data import DistribuicaoRepository

    @router.get("/exemplo")
    def exemplo(conn = Depends(get_conn)):
        repo = DistribuicaoRepository(conn)
        return repo.listar()
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator

from app.infrastructure.data import conectar


def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency: abre conexão, injeta, fecha ao fim do request."""
    conn = conectar()
    try:
        yield conn
    finally:
        conn.close()
