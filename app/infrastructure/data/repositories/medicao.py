"""MedicaoRepository — medicao_frequencia."""

from __future__ import annotations

import sqlite3


class MedicaoRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def salvar(self, records: list[tuple]) -> None:
        """Substitui todos os registros atomicamente.

        records: [(data, sg_funcao, md_cobranca, pct_cobranca), ...]
        Não faz commit — caller controla a transação.
        """
        self._conn.execute("DELETE FROM medicao_frequencia")
        self._conn.executemany(
            "INSERT INTO medicao_frequencia "
            "(data, sg_funcao, md_cobranca, pct_cobranca) VALUES (?, ?, ?, ?)",
            records,
        )

    def listar(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT data, sg_funcao, md_cobranca, pct_cobranca "
            "FROM medicao_frequencia"
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM medicao_frequencia"
        ).fetchone()[0]

    def mes_referencia(self) -> str | None:
        """YYYY-MM se todas as datas pertencem ao mesmo mês; None caso contrário.

        `data` é persistido em `dd/mm/aaaa` (ver core.normalizar_data).
        """
        rows = self._conn.execute(
            "SELECT DISTINCT substr(data, 7, 4) || '-' || substr(data, 4, 2) AS mes "
            "FROM medicao_frequencia "
            "WHERE data IS NOT NULL AND length(data) = 10"
        ).fetchall()
        if len(rows) != 1:
            return None
        return rows[0]["mes"]
