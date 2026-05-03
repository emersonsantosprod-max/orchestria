"""TreinamentosRepository — catalogo_treinamentos."""

from __future__ import annotations

import sqlite3


class TreinamentosRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def salvar(self, records: list[tuple]) -> None:
        """Substitui todos os registros atomicamente.

        records: [(nome, tipo), ...]
        Não faz commit — caller controla a transação.
        """
        self._conn.execute("DELETE FROM catalogo_treinamentos")
        self._conn.executemany(
            "INSERT INTO catalogo_treinamentos (nome, tipo) VALUES (?, ?)",
            records,
        )

    def obter(self) -> dict[str, str]:
        """Retorna {nome_upper: tipo} — implementa port TabelaClassificacao."""
        rows = self._conn.execute(
            "SELECT nome, tipo FROM catalogo_treinamentos"
        ).fetchall()
        return {r["nome"]: r["tipo"] for r in rows}

    def count(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM catalogo_treinamentos"
        ).fetchone()[0]
