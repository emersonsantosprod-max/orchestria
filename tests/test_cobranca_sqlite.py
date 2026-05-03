"""bd_cobranca SQLite path: registrar/obter + pipeline fallback."""

import openpyxl
import pytest

from app.infrastructure import data


def _make_base_cobranca_xlsx(tmp_path, rows):
    path = tmp_path / "base_cobranca.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    wb.save(path)
    return str(path)


@pytest.fixture
def conn(tmp_path):
    c = data.conectar(str(tmp_path / "test.db"))
    yield c
    c.close()


def test_registrar_cobranca_popula_e_obter_retorna_dict(tmp_path, conn):
    path = _make_base_cobranca_xlsx(tmp_path, [
        ["MECANICO",         "FÉRIAS C/ DESC"],
        ["ELETRICISTA",      "FÉRIAS S/ DESC"],
        ["AJUDANTE",         "OUTRO"],
    ])
    data.registrar_cobranca(path, conn)

    dado = data.obter_cobranca(conn)
    assert dado == {
        'MECANICO':    'FÉRIAS C/ DESC',
        'ELETRICISTA': 'FÉRIAS S/ DESC',
        'AJUDANTE':    'OUTRO',
    }


def test_registrar_cobranca_idempotente_substitui(tmp_path, conn):
    p1 = _make_base_cobranca_xlsx(tmp_path, [["A", "X"]])
    data.registrar_cobranca(p1, conn)
    p2 = _make_base_cobranca_xlsx(tmp_path, [["B", "Y"], ["C", "Z"]])
    data.registrar_cobranca(p2, conn)
    assert data.obter_cobranca(conn) == {'B': 'Y', 'C': 'Z'}


def test_obter_cobranca_vazio_retorna_dict_vazio(conn):
    assert data.obter_cobranca(conn) == {}


def test_popular_cobranca_se_vazio_no_op_quando_ja_populada(tmp_path, conn):
    path = _make_base_cobranca_xlsx(tmp_path, [["A", "X"]])
    data.registrar_cobranca(path, conn)
    other = _make_base_cobranca_xlsx(tmp_path, [["B", "Y"]])
    assert data.popular_cobranca_se_vazio(conn, other) is False
    assert data.obter_cobranca(conn) == {'A': 'X'}


def test_popular_cobranca_se_vazio_no_op_sem_xlsx(conn):
    assert data.popular_cobranca_se_vazio(conn, None) is False


def test_popular_cobranca_se_vazio_popula_quando_vazia(tmp_path, conn):
    path = _make_base_cobranca_xlsx(tmp_path, [["A", "X"]])
    assert data.popular_cobranca_se_vazio(conn, path) is True
    assert data.obter_cobranca(conn) == {'A': 'X'}


def test_loaders_xlsx_e_sqlite_produzem_mesmo_dict(tmp_path, conn):
    """Equivalence: xlsx-derived dict == SQLite-derived dict."""
    from app.infrastructure import loaders
    path = _make_base_cobranca_xlsx(tmp_path, [
        ["MECANICO",    "FÉRIAS C/ DESC"],
        ["ELETRICISTA", "FÉRIAS S/ DESC"],
    ])
    via_xlsx = loaders.carregar_base_cobranca_xlsx(path)
    data.registrar_cobranca(path, conn)
    via_sqlite = data.obter_cobranca(conn)
    assert via_xlsx == via_sqlite
