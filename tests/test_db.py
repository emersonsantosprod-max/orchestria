import openpyxl
import pytest

from app import db


def _make_base_treinamentos_xlsx(tmp_path, rows):
    path = tmp_path / "base_treinamentos.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Treinamento", "Tipo", "Carga Horaria"])
    for row in rows:
        ws.append(row)
    wb.save(path)
    return str(path)


@pytest.fixture
def conn(tmp_path):
    c = db.conectar(str(tmp_path / "test.db"))
    yield c
    c.close()


def test_registrar_base_treinamentos_popula_tabela(tmp_path, conn):
    path = _make_base_treinamentos_xlsx(tmp_path, [
        ["NR-10", "Remunerado", "8H"],
        ["NR-35", "Não remunerado", "4H"],
    ])
    db.registrar_base_treinamentos(path, conn)
    rows = conn.execute("SELECT nome, tipo FROM bd_treinamentos ORDER BY nome").fetchall()
    assert len(rows) == 2
    assert rows[0]["nome"] == "NR-10"
    assert rows[0]["tipo"] == "remunerado"
    assert rows[1]["nome"] == "NR-35"
    assert rows[1]["tipo"] == "nao_remunerado"


def test_registrar_base_treinamentos_registra_arquivo(tmp_path, conn):
    path = _make_base_treinamentos_xlsx(tmp_path, [["NR-10", "Remunerado", "8H"]])
    db.registrar_base_treinamentos(path, conn)
    reg = conn.execute(
        "SELECT tipo FROM registro_arquivos WHERE tipo='treinamentos'"
    ).fetchone()
    assert reg is not None


def test_obter_tabela_treinamento_retorna_dict_nome_tipo(tmp_path, conn):
    path = _make_base_treinamentos_xlsx(tmp_path, [
        ["NR-10", "Remunerado", "8H"],
        ["NR-35", "Não remunerado", "4H"],
    ])
    db.registrar_base_treinamentos(path, conn)
    tabela = db.obter_tabela_treinamento(conn)
    assert tabela == {"NR-10": "remunerado", "NR-35": "nao_remunerado"}


def test_obter_tabela_treinamento_retorna_vazio_se_nao_registrada(conn):
    tabela = db.obter_tabela_treinamento(conn)
    assert tabela == {}


def test_popular_treinamentos_se_vazio_popula_tabela(tmp_path, conn, monkeypatch):
    from pathlib import Path
    xlsx = _make_base_treinamentos_xlsx(tmp_path, [
        ["NR-10", "Remunerado", "8H"],
        ["NR-35", "Não remunerado", "4H"],
    ])
    monkeypatch.setattr(db, 'bundled_treinamentos_xlsx', lambda: Path(xlsx))
    result = db.popular_treinamentos_se_vazio(conn)
    assert result is True
    tabela = db.obter_tabela_treinamento(conn)
    assert len(tabela) == 2


def test_popular_treinamentos_se_vazio_idempotente_com_dados(tmp_path, conn, monkeypatch):
    from pathlib import Path
    xlsx = _make_base_treinamentos_xlsx(tmp_path, [["NR-10", "Remunerado", "8H"]])
    monkeypatch.setattr(db, 'bundled_treinamentos_xlsx', lambda: Path(xlsx))
    db.popular_treinamentos_se_vazio(conn)
    result = db.popular_treinamentos_se_vazio(conn)
    assert result is False


def test_popular_treinamentos_se_vazio_idempotente_com_registro(tmp_path, conn, monkeypatch):
    from pathlib import Path
    xlsx = _make_base_treinamentos_xlsx(tmp_path, [["NR-10", "Remunerado", "8H"]])
    monkeypatch.setattr(db, 'bundled_treinamentos_xlsx', lambda: Path(xlsx))
    db.registrar_base_treinamentos(xlsx, conn)
    result = db.popular_treinamentos_se_vazio(conn)
    assert result is False


def test_popular_treinamentos_se_vazio_sem_xlsx_bundled(tmp_path, conn, monkeypatch):
    monkeypatch.setattr(db, 'bundled_treinamentos_xlsx', lambda: tmp_path / 'inexistente.xlsx')
    result = db.popular_treinamentos_se_vazio(conn)
    assert result is False
    assert db.obter_tabela_treinamento(conn) == {}
