import tempfile

import openpyxl
import pytest

from app.infrastructure.db import (
    _normalizar_pct,
    conectar,
    obter_bd,
    obter_medicao,
    registrar_bd,
    registrar_medicao,
)
from app.domain.distribuicao import (
    ERRO_EXCESSO_RATEIO,
    ERRO_INSUFICIENCIA_RATEIO,
    ERRO_LINHA_AUSENTE,
    validar_aderencia_distribuicao,
)


def _make_bd_xlsx(rows: list[tuple]) -> str:
    """Create temp BD xlsx with header + rows: (funcao, md_cobranca, area, quantidade)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['funcao', 'md_cobranca', 'area', 'quantidade'])
    for row in rows:
        ws.append(list(row))
    tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    wb.save(tmp.name)
    tmp.close()
    return tmp.name


def _make_medicao_xlsx(rows: list[tuple]) -> str:
    """Create temp Medição xlsx with Frequencia sheet.
    rows: (data, sg_funcao, md_cobranca, pct_cobranca)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Frequencia'
    ws.append(['Data', 'RE', 'Nome', 'Sg Função', 'Unidade', 'MD Cobranca', '% Cobrança'])
    for data, sg_funcao, md_cobranca, pct in rows:
        ws.append([data, '12345', 'Nome Teste', sg_funcao, 'UNID', md_cobranca, pct])
    tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    wb.save(tmp.name)
    tmp.close()
    return tmp.name


def _mem_conn():
    """In-memory SQLite connection with schema applied."""
    return conectar(':memory:')


def test_normalizar_pct_ja_normalizado():
    assert _normalizar_pct(1.0) == 1.0
    assert _normalizar_pct(0.45) == 0.45
    assert _normalizar_pct(0.0) == 0.0


def test_normalizar_pct_escala_100():
    assert _normalizar_pct(100.0) == pytest.approx(1.0)
    assert _normalizar_pct(45.0)  == pytest.approx(0.45)
    assert _normalizar_pct(50.0)  == pytest.approx(0.5)


def test_normalizar_pct_none():
    assert _normalizar_pct(None) == 0.0


def test_normalizar_pct_limite_exato():
    # 1.0 ≤ 1.0 → não divide
    assert _normalizar_pct(1.0) == 1.0
    # 1.01 > 1.0 → divide
    assert _normalizar_pct(1.01) == pytest.approx(0.0101)


def test_registrar_bd_round_trip():
    path = _make_bd_xlsx([
        ('AUDITOR', 'CENTRAL', None, 3.0),
        ('AUDITOR', 'BREAKDOWN', 'PE-1', 0.5),
    ])
    conn = _mem_conn()
    registrar_bd(path, conn)
    rows = obter_bd(conn)
    assert len(rows) == 2
    assert rows[0]['funcao'] == 'AUDITOR'
    assert rows[0]['md_cobranca'] == 'CENTRAL'
    assert rows[0]['quantidade'] == 3.0


def test_registrar_bd_limpa_anterior():
    path = _make_bd_xlsx([('AUDITOR', 'CENTRAL', None, 3.0)])
    conn = _mem_conn()
    registrar_bd(path, conn)
    path2 = _make_bd_xlsx([('INSPETOR', 'HD', None, 2.0)])
    registrar_bd(path2, conn)
    rows = obter_bd(conn)
    assert len(rows) == 1
    assert rows[0]['funcao'] == 'INSPETOR'


def test_registrar_medicao_round_trip():
    path = _make_medicao_xlsx([
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
    ])
    conn = _mem_conn()
    registrar_medicao(path, conn)
    rows = obter_medicao(conn)
    assert len(rows) == 2
    assert rows[0]['data'] == '01/04/2026'
    assert rows[0]['sg_funcao'] == 'AUDITOR'
    assert rows[0]['pct_cobranca'] == 1.0


def test_registrar_medicao_normaliza_pct_escala_100():
    path = _make_medicao_xlsx([('01/04/2026', 'AUDITOR', 'CENTRAL', 100.0)])
    conn = _mem_conn()
    registrar_medicao(path, conn)
    rows = obter_medicao(conn)
    assert rows[0]['pct_cobranca'] == pytest.approx(1.0)


def test_registrar_medicao_aviso_escala_mista():
    path = _make_medicao_xlsx([
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'INSPETOR', 'HD', 100.0),
    ])
    conn = _mem_conn()
    avisos = registrar_medicao(path, conn)
    assert any('AVISO_ESCALA_INDEFINIDA' in av for av in avisos)


def test_registrar_medicao_sem_aviso_escala_uniforme():
    path = _make_medicao_xlsx([
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'INSPETOR', 'HD', 0.5),
    ])
    conn = _mem_conn()
    avisos = registrar_medicao(path, conn)
    assert not any('AVISO_ESCALA_INDEFINIDA' in av for av in avisos)


def _bd(rows):
    return [{'funcao': f, 'md_cobranca': m, 'area': a, 'quantidade': q}
            for f, m, a, q in rows]

def _med(rows):
    return [{'data': d, 'sg_funcao': f, 'md_cobranca': m, 'pct_cobranca': p}
            for d, f, m, p in rows]


def test_validar_sem_inconsistencias():
    bd  = _bd([('AUDITOR', 'CENTRAL', None, 3.0)])
    med = _med([
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
    ])
    result = validar_aderencia_distribuicao(bd, med)
    assert result == []


def test_validar_erro_insuficiencia_rateio():
    bd  = _bd([('AUDITOR', 'CENTRAL', None, 3.0)])
    med = _med([
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
    ])
    result = validar_aderencia_distribuicao(bd, med)
    assert len(result) == 1
    inc = result[0]
    assert inc.tipo_inconsistencia == ERRO_INSUFICIENCIA_RATEIO
    assert inc.esperado  == pytest.approx(3.0)
    assert inc.realizado == pytest.approx(2.0)
    assert inc.diff      == pytest.approx(-1.0)


def test_validar_erro_excesso_rateio():
    bd  = _bd([('AUDITOR', 'CENTRAL', None, 2.0)])
    med = _med([
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
    ])
    result = validar_aderencia_distribuicao(bd, med)
    assert len(result) == 1
    assert result[0].tipo_inconsistencia == ERRO_EXCESSO_RATEIO
    assert result[0].diff == pytest.approx(1.0)


def test_validar_erro_linha_ausente_md_cobranca():
    """funcao presente no dia, mas md_cobranca esperado ausente → ERRO_LINHA_AUSENTE."""
    bd  = _bd([
        ('AUDITOR', 'CENTRAL',   None, 2.0),
        ('AUDITOR', 'BREAKDOWN', None, 1.0),
    ])
    med = _med([
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        # AUDITOR/BREAKDOWN ausente, mas AUDITOR existe no dia
    ])
    result = validar_aderencia_distribuicao(bd, med)
    assert len(result) == 1
    inc = result[0]
    assert inc.tipo_inconsistencia == ERRO_LINHA_AUSENTE
    assert inc.funcao == 'AUDITOR'
    assert inc.md_cobranca == 'BREAKDOWN'
    assert inc.realizado == 0.0


def test_validar_sem_erro_funcao_totalmente_ausente():
    """funcao completamente ausente da Medição no dia → NÃO gera inconsistência."""
    bd  = _bd([('AUDITOR', 'CENTRAL', None, 3.0)])
    med = _med([
        ('01/04/2026', 'INSPETOR', 'HD', 1.0),
        # AUDITOR ausente no dia; INSPETOR não tem contrato BD
    ])
    result = validar_aderencia_distribuicao(bd, med)
    assert result == []


def test_validar_sem_data_sintetica():
    """Datas vêm apenas da Medição; BD não gera datas."""
    bd  = _bd([('AUDITOR', 'CENTRAL', None, 3.0)])
    # Medição só tem data 02/04 — não deve haver inconsistência para 01/04
    med = _med([
        ('02/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('02/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
        ('02/04/2026', 'AUDITOR', 'CENTRAL', 1.0),
    ])
    result = validar_aderencia_distribuicao(bd, med)
    assert result == []  # 02/04 match; 01/04 não existe → sem inconsistência


def test_validar_bd_agrega_area():
    """BD com múltiplas áreas para mesma (funcao, md_cobranca) é somado."""
    bd  = _bd([
        ('ASS-ADM', 'BREAKDOWN', 'PE-1',  0.35),
        ('ASS-ADM', 'BREAKDOWN', 'PE-2',  0.35),
        ('ASS-ADM', 'BREAKDOWN', 'IESE',  0.45),
    ])
    total = 0.35 + 0.35 + 0.45  # 1.15
    med = _med([('01/04/2026', 'ASS-ADM', 'BREAKDOWN', total)])
    result = validar_aderencia_distribuicao(bd, med)
    assert result == []


def test_validar_precisao_float():
    """round(realizado - esperado, 10) não gera falso positivo por ruído float."""
    # 0.1 + 0.2 em float puro ≠ 0.3, mas round(x, 10) deve absorver
    bd  = _bd([('FUNC', 'MD', None, 0.3)])
    med = _med([
        ('01/04/2026', 'FUNC', 'MD', 0.1),
        ('01/04/2026', 'FUNC', 'MD', 0.1),
        ('01/04/2026', 'FUNC', 'MD', 0.1),
    ])
    result = validar_aderencia_distribuicao(bd, med)
    assert result == []


def test_validar_ordenacao_deterministica():
    """Saída ordenada por (data, funcao, md_cobranca), independente da ordem de entrada."""
    bd  = _bd([
        ('ZULTO',   'CENTRAL', None, 10.0),
        ('AARDVARK', 'CENTRAL', None, 10.0),
    ])
    med = _med([
        ('02/04/2026', 'ZULTO',    'CENTRAL', 1.0),
        ('01/04/2026', 'AARDVARK', 'CENTRAL', 1.0),
        ('01/04/2026', 'ZULTO',    'CENTRAL', 1.0),
        ('02/04/2026', 'AARDVARK', 'CENTRAL', 1.0),
    ])
    result = validar_aderencia_distribuicao(bd, med)
    keys = [(i.data, i.funcao) for i in result]
    assert keys == sorted(keys)


def test_validar_multiplas_datas_independentes():
    """Cada data é validada independentemente — sem compensação entre datas."""
    bd  = _bd([('AUDITOR', 'CENTRAL', None, 2.0)])
    med = _med([
        ('01/04/2026', 'AUDITOR', 'CENTRAL', 1.0),   # falta 1 no dia 01
        ('02/04/2026', 'AUDITOR', 'CENTRAL', 1.0),   # falta 1 no dia 02
        ('02/04/2026', 'AUDITOR', 'CENTRAL', 1.0),   # ainda falta 1 → mas soma a 2 → OK
    ])
    result = validar_aderencia_distribuicao(bd, med)
    # 01/04 → realizado=1 < esperado=2 → ERRO_INSUFICIENCIA_RATEIO
    # 02/04 → realizado=2 = esperado=2 → OK
    assert len(result) == 1
    assert result[0].data == '01/04/2026'
    assert result[0].tipo_inconsistencia == ERRO_INSUFICIENCIA_RATEIO
