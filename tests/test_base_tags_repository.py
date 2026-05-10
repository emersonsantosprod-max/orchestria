"""BaseTagsRepository: salvar/todos/count + replace atômico."""

import pytest

from app.infrastructure.data import BaseTagsRepository, conectar


@pytest.fixture
def conn():
    c = conectar(":memory:")
    yield c
    c.close()


def test_count_empty(conn):
    assert BaseTagsRepository(conn).count() == 0


def test_salvar_e_todos(conn):
    repo = BaseTagsRepository(conn)
    repo.salvar([
        ('MECANICO', 'UNIDADE A', 'PACOTE', 'FERIAS', 'TAG-1'),
        ('SOLDADOR', 'UNIDADE B', 'ADICIONAL', 'FERIAS S/ DESC', 'TAG-2'),
    ])
    out = repo.todos()
    assert out == {
        ('MECANICO', 'UNIDADE A', 'PACOTE', 'FERIAS'): 'TAG-1',
        ('SOLDADOR', 'UNIDADE B', 'ADICIONAL', 'FERIAS S/ DESC'): 'TAG-2',
    }
    assert repo.count() == 2


def test_salvar_substitui_atomicamente(conn):
    repo = BaseTagsRepository(conn)
    repo.salvar([('A', 'B', 'C', 'D', 'OLD')])
    repo.salvar([('X', 'Y', 'Z', 'W', 'NEW')])
    assert repo.todos() == {('X', 'Y', 'Z', 'W'): 'NEW'}


def test_chave_composta_pk(conn):
    import sqlite3
    repo = BaseTagsRepository(conn)
    with pytest.raises(sqlite3.IntegrityError):
        repo.salvar([
            ('A', 'B', 'C', 'D', 'T1'),
            ('A', 'B', 'C', 'D', 'T2'),  # PK duplicada
        ])
