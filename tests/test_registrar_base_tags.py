"""Loader registrar_base_tags: happy path, sem dados, header opcional, dedup."""

from pathlib import Path

import openpyxl
import pytest

from app.domain.errors import PlanilhaInvalidaError
from app.infrastructure.data import (
    BaseTagsRepository,
    RegistryRepository,
    conectar,
    registrar_base_tags,
)


@pytest.fixture
def conn():
    c = conectar(":memory:")
    yield c
    c.close()


def _criar_xlsx(tmp_path: Path, rows: list[list]) -> Path:
    p = tmp_path / "tags.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    wb.save(p)
    return p


def test_happy_path_com_header(tmp_path, conn):
    p = _criar_xlsx(tmp_path, [
        ['SG Função', 'Unidade', 'MD Cobrança', 'Situação', 'Tag'],
        ['Mecânico', 'Unidade-A', 'PACOTE', 'Férias', 'M-PACO-FE'],
        ['Soldador', 'Unidade-B', 'ADICIONAL', 'Férias S/ Desc', 'S-ADIC-FE'],
    ])
    registrar_base_tags(p, conn)
    repo = BaseTagsRepository(conn)
    assert repo.todos() == {
        ('MECANICO', 'UNIDADE-A', 'PACOTE', 'FERIAS'): 'M-PACO-FE',
        ('SOLDADOR', 'UNIDADE-B', 'ADICIONAL', 'FERIAS S/ DESC'): 'S-ADIC-FE',
    }
    reg = RegistryRepository(conn).get('tags')
    assert reg is not None
    assert reg['caminho'] == str(p)


def test_sem_header(tmp_path, conn):
    p = _criar_xlsx(tmp_path, [
        ['MECANICO', 'A', 'PACOTE', 'FERIAS', 'M-A-PA-FE'],
    ])
    registrar_base_tags(p, conn)
    assert BaseTagsRepository(conn).todos() == {
        ('MECANICO', 'A', 'PACOTE', 'FERIAS'): 'M-A-PA-FE',
    }


def test_sem_dados(tmp_path, conn):
    p = _criar_xlsx(tmp_path, [
        ['SG Função', 'Unidade', 'MD Cobrança', 'Situação', 'Tag'],
    ])
    with pytest.raises(PlanilhaInvalidaError):
        registrar_base_tags(p, conn)


def test_dedupe_chave_repetida(tmp_path, conn):
    """Linhas duplicadas (mesma chave normalizada) usam a primeira ocorrência."""
    p = _criar_xlsx(tmp_path, [
        ['Mecânico', 'A', 'PACOTE', 'Férias', 'PRIMEIRA'],
        ['MECANICO', 'A', 'pacote', 'FÉRIAS', 'SEGUNDA'],
    ])
    registrar_base_tags(p, conn)
    assert BaseTagsRepository(conn).todos() == {
        ('MECANICO', 'A', 'PACOTE', 'FERIAS'): 'PRIMEIRA',
    }


def test_linhas_incompletas_ignoradas(tmp_path, conn):
    p = _criar_xlsx(tmp_path, [
        ['Mecânico', 'A', 'PACOTE', 'Férias', 'OK'],
        ['', '', '', '', ''],
        ['Mecânico', 'A', 'PACOTE', '', 'X'],
    ])
    registrar_base_tags(p, conn)
    assert BaseTagsRepository(conn).count() == 1
