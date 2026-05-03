"""DistribuicaoRepository — bd_distribuicao."""

from __future__ import annotations

import sqlite3


class DistribuicaoRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def salvar(self, records: list[tuple]) -> None:
        """Substitui todos os registros atomicamente.

        records: [(funcao, md_cobranca, area, quantidade), ...]
        Não faz commit — caller controla a transação.
        """
        self._conn.execute("DELETE FROM bd_distribuicao")
        self._conn.executemany(
            "INSERT INTO bd_distribuicao (funcao, md_cobranca, area, quantidade) "
            "VALUES (?, ?, ?, ?)",
            records,
        )

    def listar(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT funcao, md_cobranca, area, quantidade FROM bd_distribuicao"
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM bd_distribuicao"
        ).fetchone()[0]
