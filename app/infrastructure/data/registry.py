"""
registry.py — RegistryRepository: tabela de controle de arquivos importados.

Usado por GET /api/initial-data para derivar os estados de UI:
  catalog_status, measurement_status.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

class RegistryRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get(self, tipo: str) -> dict | None:
        """Retorna {'caminho': str, 'importado_em': str} ou None se ausente."""
        row = self._conn.execute(
            "SELECT caminho, importado_em FROM registro_arquivos WHERE tipo = ?",
            (tipo,),
        ).fetchone()
        return dict(row) if row else None

    def get_all(self) -> dict[str, dict]:
        """Retorna {tipo: {'caminho': str, 'importado_em': str}}."""
        rows = self._conn.execute(
            "SELECT tipo, caminho, importado_em FROM registro_arquivos"
        ).fetchall()
        return {
            r["tipo"]: {"caminho": r["caminho"], "importado_em": r["importado_em"]}
            for r in rows
        }

    def upsert(self, tipo: str, caminho: str) -> None:
        """Registra ou atualiza entrada. Não faz commit — caller é responsável."""
        self._conn.execute(
            "INSERT OR REPLACE INTO registro_arquivos (tipo, caminho, importado_em) "
            "VALUES (?, ?, ?)",
            (tipo, caminho, datetime.now().isoformat()),
        )
