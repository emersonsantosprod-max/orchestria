"""FeriasRepository — regras_pagamento_ferias."""

from __future__ import annotations

import sqlite3


class FeriasRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def salvar(self, records: list[tuple]) -> None:
        """Substitui todos os registros atomicamente.

        records: [(sg_funcao, md_cobranca, remunerado), ...]
        Não faz commit — caller controla a transação.
        """
        self._conn.execute("DELETE FROM regras_pagamento_ferias")
        self._conn.executemany(
            "INSERT INTO regras_pagamento_ferias (sg_funcao, md_cobranca, remunerado) "
            "VALUES (?, ?, ?)",
            records,
        )

    def obter_mapa(self) -> dict[str, str]:
        """Retorna {sg_funcao_upper: md_cobranca_upper}.

        Mesmo contrato consumido por ferias.gerar_updates_ferias.
        """
        rows = self._conn.execute(
            "SELECT sg_funcao, md_cobranca FROM regras_pagamento_ferias"
        ).fetchall()
        return {r["sg_funcao"]: r["md_cobranca"] for r in rows}

    def count(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM regras_pagamento_ferias"
        ).fetchone()[0]
