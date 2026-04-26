"""
Integração adapter→domínio (sem comparação com legado).

Exercita o pipeline completo:
``ler_xlsx_contratual → parse_distribuicao_cols → normalizar_linhas →
validar_distribuicao_cobranca`` numa entrada controlada e valida
estruturalmente as saídas. Persiste no steady state pós-Step 6.
"""

from __future__ import annotations

import openpyxl
import pytest

from app.domain.distribuicao_contratual import (
    AVISO_DECIMAL,
    AVISO_DISCREPANCIA_ATUAL,
    ERRO_SIGLA,
    ERRO_TOTAL,
    localizar_colunas_chave,
    normalizar_linhas,
    parse_distribuicao_cols,
    validar_distribuicao_cobranca,
)
from app.infrastructure.adapters.excel_distribuicao_contratual import (
    ler_xlsx_contratual,
)

_PUBLISHED_TIPOS = {
    ERRO_SIGLA, ERRO_TOTAL, AVISO_DECIMAL, AVISO_DISCREPANCIA_ATUAL,
    'AVISO_SIGLA_DUPLICADA', 'AVISO_COLUNA_DESCONHECIDA',
    'AVISO_COLUNA_DUPLICADA', 'AVISO_VALOR_NAO_NUMERICO',
    'AVISO_HEADER_DUPLICADO',
}


@pytest.fixture(scope='module')
def integration_xlsx(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp('int_dc') / 'integration_min.xlsx'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['TP MO', 'FUNÇÃO', 'SIGLA', 'CENTRAL', 'BREAKDOWN PE1', 'Atual'])
    ws.append(['MOD', 'ELETRICISTA I', 'ELET-I', 5, 1, 6])
    ws.append(['MOD', 'MECANICO II',   'MEC-II', 3, 0, 3])
    wb.save(path)
    wb.close()
    return str(path)


def test_pipeline_adapter_dominio(integration_xlsx):
    headers, data_rows, w_hdr = ler_xlsx_contratual(integration_xlsx)
    col_map, w0 = parse_distribuicao_cols(headers)
    sigla_col, funcao_col, atual_col = localizar_colunas_chave(headers)
    normalized, raw_sums, atual, w1 = normalizar_linhas(
        data_rows, col_map, sigla_col, funcao_col, atual_col)
    incons = validar_distribuicao_cobranca(normalized, raw_sums, atual)

    assert len(normalized) > 0
    for r in normalized:
        assert set(r.keys()) == {'funcao', 'md_cobranca', 'area', 'quantidade'}
        assert isinstance(r['funcao'], str) and r['funcao'].isupper()
        assert isinstance(r['md_cobranca'], str)
        assert isinstance(r['quantidade'], (int, float))

    assert {k.isupper() and isinstance(k, str) for k in raw_sums} == {True}
    assert all(isinstance(v, (int, float)) for v in raw_sums.values())

    for w in w_hdr + w0 + w1 + incons:
        assert w['tipo'] in _PUBLISHED_TIPOS

    by_key = {(r['funcao'], r['md_cobranca'], r['area']): r['quantidade'] for r in normalized}
    assert by_key[('ELET-I', 'BREAKDOWN', 'PE-1')] == 1
    assert by_key[('ELET-I', 'CENTRAL', None)] == 5
