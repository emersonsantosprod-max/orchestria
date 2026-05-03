"""
schema.py — DDL do banco. Chamado uma vez no boot pelo composition root.

Regra: nenhum outro módulo executa CREATE TABLE.
"""

from __future__ import annotations

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bd_distribuicao (
    funcao      TEXT NOT NULL,
    md_cobranca TEXT NOT NULL,
    area        TEXT,
    quantidade  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS medicao_frequencia (
    data         TEXT NOT NULL,
    sg_funcao    TEXT NOT NULL,
    md_cobranca  TEXT NOT NULL,
    pct_cobranca REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS catalogo_treinamentos (
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS regras_pagamento_ferias (
    sg_funcao   TEXT NOT NULL,
    md_cobranca TEXT NOT NULL,
    remunerado  INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS registro_arquivos (
    tipo         TEXT PRIMARY KEY,
    caminho      TEXT NOT NULL,
    importado_em TEXT NOT NULL
);
"""


def create_schema(conn: sqlite3.Connection) -> None:
    """Aplica DDL idempotente. Chamar apenas no bootstrap do composition root."""
    conn.executescript(_SCHEMA)
    conn.commit()
