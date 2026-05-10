"""BaseTagsRepository — tabela base_tags.

Lookup de TAG por chave (sg_funcao, unidade, md_cobranca, situacao).
Chaves são armazenadas já normalizadas (NFKD + accent-fold + UPPER) —
loader chama `app.domain.normalizacao.normalizar` antes de inserir.
"""

from __future__ import annotations

import sqlite3


class BaseTagsRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def salvar(self, records: list[tuple]) -> None:
        """Substitui todos os registros atomicamente.

        records: [(sg_funcao, unidade, md_cobranca, situacao, tag), ...]
        Caller controla a transação — não comita.
        """
        self._conn.execute("DELETE FROM base_tags")
        self._conn.executemany(
            "INSERT INTO base_tags "
            "(sg_funcao, unidade, md_cobranca, situacao, tag) "
            "VALUES (?, ?, ?, ?, ?)",
            records,
        )

    def todos(self) -> dict[tuple[str, str, str, str], str]:
        """Retorna {(sg_funcao, unidade, md_cobranca, situacao): tag}."""
        rows = self._conn.execute(
            "SELECT sg_funcao, unidade, md_cobranca, situacao, tag "
            "FROM base_tags"
        ).fetchall()
        return {
            (r["sg_funcao"], r["unidade"], r["md_cobranca"], r["situacao"]): r["tag"]
            for r in rows
        }

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM base_tags").fetchone()[0]
