"""TreinamentosRepository implements port TabelaClassificacao via .obter()."""

import sqlite3

from app.infrastructure.data import TreinamentosRepository, create_schema


def _seed_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    conn.executemany(
        "INSERT INTO catalogo_treinamentos(nome, tipo) VALUES (?, ?)",
        [('NR-10 BÁSICO', 'NR-10'), ('NR-35', 'NR-35')],
    )
    conn.commit()
    return conn


def test_repository_devolve_mapping_da_tabela():
    conn = _seed_conn()
    try:
        tabela = TreinamentosRepository(conn).obter()
        assert tabela == {'NR-10 BÁSICO': 'NR-10', 'NR-35': 'NR-35'}
    finally:
        conn.close()


def test_repository_devolve_dict_vazio_quando_tabela_vazia():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    try:
        assert TreinamentosRepository(conn).obter() == {}
    finally:
        conn.close()
