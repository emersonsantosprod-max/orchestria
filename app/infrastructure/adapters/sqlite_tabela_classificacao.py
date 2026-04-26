"""Adapter SQLite do port TabelaClassificacao.

Wraps app.db.obter_tabela_treinamento(conn). Construído pela composition root
(app/main.py, ui/gui.py) e injetado em LancarTreinamentosService.
"""

import sqlite3
from collections.abc import Mapping

from app import db


class SqliteTabelaClassificacao:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def obter(self) -> Mapping[str, str]:
        return db.obter_tabela_treinamento(self._conn)
