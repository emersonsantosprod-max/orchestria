import os
import tempfile

import openpyxl

from app.distribuicao_contratual import (
    AVISO_COLUNA_DESCONHECIDA,
    AVISO_DECIMAL,
    AVISO_DISCREPANCIA_ATUAL,
    ERRO_SIGLA,
    ERRO_TOTAL,
    carregar_e_normalizar,
    normalize_area,
    parse_distribuicao_cols,
    validar_distribuicao_cobranca,
)

# ---------------------------------------------------------------------------
# normalize_area
# ---------------------------------------------------------------------------

def test_normalize_area():
    assert normalize_area('PE1') == 'PE-1'
    assert normalize_area('PE2') == 'PE-2'
    assert normalize_area('PE3') == 'PE-3'
    assert normalize_area('PVC') == 'PVC'
    assert normalize_area('UO') == 'UO'
    assert normalize_area('UA') == 'UA'
    assert normalize_area('IESE') == 'IESE'
    assert normalize_area('TEGAL') == 'TEGAL'
    assert normalize_area('ANALITICA') == 'ANALITICA'


# ---------------------------------------------------------------------------
# parse_distribuicao_cols
# ---------------------------------------------------------------------------

_FULL_HEADERS = (
    'TP MO', 'ÁREA', 'FUNÇÃO', 'SIGLA',
    'CENTRAL', 'ADM-B',
    'BREAKDOWN PE1', 'BREAKDOWN PE2', 'BREAKDOWN PE3',
    'HD PE3', 'CV PE3', 'HD PVC', 'BREAKDOWN PVC',
    'BREAKDOWN UO', 'CV UO', 'BREAKDOWN UA', 'CV UA',
    'BREAKDOWN IESE', 'CV IESE', 'BREAKDOWN TEGAL',
    'ANALITICA', 'INSPEÇÃO', 'Atual', 'OBSERVAÇÕES',
)


def test_parse_distribuicao_cols_known_headers():
    col_map, warnings = parse_distribuicao_cols(_FULL_HEADERS)
    h = _FULL_HEADERS

    assert col_map[h.index('CENTRAL')]        == ('CENTRAL', None)
    assert col_map[h.index('ADM-B')]          == ('ADM-B', None)
    assert col_map[h.index('ANALITICA')]      == ('BREAKDOWN', 'ANALITICA')
    assert col_map[h.index('BREAKDOWN PE1')]  == ('BREAKDOWN', 'PE-1')
    assert col_map[h.index('BREAKDOWN PE2')]  == ('BREAKDOWN', 'PE-2')
    assert col_map[h.index('BREAKDOWN PE3')]  == ('BREAKDOWN', 'PE-3')
    assert col_map[h.index('HD PE3')]         == ('HD', 'PE-3')
    assert col_map[h.index('CV PE3')]         == ('CV', 'PE-3')
    assert col_map[h.index('HD PVC')]         == ('HD', 'PVC')
    assert col_map[h.index('BREAKDOWN PVC')]  == ('BREAKDOWN', 'PVC')
    assert col_map[h.index('CV UO')]          == ('CV', 'UO')
    assert not warnings


def test_parse_distribuicao_cols_skips_non_distribution():
    col_map, _ = parse_distribuicao_cols(_FULL_HEADERS)
    h = _FULL_HEADERS
    for name in ('TP MO', 'ÁREA', 'FUNÇÃO', 'SIGLA', 'INSPEÇÃO', 'Atual', 'OBSERVAÇÕES'):
        assert h.index(name) not in col_map


def test_parse_distribuicao_cols_unknown_header():
    headers = ('SIGLA', 'CENTRAL', 'COLUNA_ESTRANHA')
    col_map, warnings = parse_distribuicao_cols(headers)
    assert 2 not in col_map
    assert any(w['tipo'] == AVISO_COLUNA_DESCONHECIDA for w in warnings)


# ---------------------------------------------------------------------------
# Helpers for mock workbook tests
# ---------------------------------------------------------------------------

def _make_workbook(rows: list) -> str:
    fd, path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    wb.save(path)
    wb.close()
    return path


# ---------------------------------------------------------------------------
# carregar_e_normalizar
# ---------------------------------------------------------------------------

def test_normalizar_amostra():
    path = _make_workbook([
        ['TP MO', 'ÁREA', 'FUNÇÃO', 'SIGLA', 'CENTRAL', 'BREAKDOWN PVC', 'BREAKDOWN UA', 'Atual'],
        ['MOD', 'ELÉTRICA', 'ELETRICISTA I', 'ELET-I', 5, 2, 1, 8],
    ])
    try:
        normalized, raw_sums, atual, warnings = carregar_e_normalizar(path)
    finally:
        os.unlink(path)

    assert len(normalized) == 3
    by_key = {(r['md_cobranca'], r['area']): r['quantidade'] for r in normalized}
    assert by_key[('CENTRAL', None)] == 5
    assert by_key[('BREAKDOWN', 'PVC')] == 2
    assert by_key[('BREAKDOWN', 'UA')] == 1
    assert all(r['funcao'] == 'ELET-I' for r in normalized)
    assert raw_sums['ELET-I'] == 8
    assert atual['ELET-I'] == 8.0
    assert not any(w['tipo'] in (ERRO_SIGLA, ERRO_TOTAL) for w in warnings)


def test_normalizar_skip_zero():
    path = _make_workbook([
        ['SIGLA', 'CENTRAL', 'BREAKDOWN PE1'],
        ['ELET-I', 0, None],
    ])
    try:
        normalized, raw_sums, _, _ = carregar_e_normalizar(path)
    finally:
        os.unlink(path)

    assert normalized == []
    assert raw_sums.get('ELET-I', 0) == 0


def test_normalizar_aviso_decimal():
    path = _make_workbook([
        ['SIGLA', 'CENTRAL'],
        ['ELET-I', 1.5],
    ])
    try:
        normalized, _, _, warnings = carregar_e_normalizar(path)
    finally:
        os.unlink(path)

    assert len(normalized) == 1
    assert normalized[0]['quantidade'] == 1.5
    assert any(w['tipo'] == AVISO_DECIMAL for w in warnings)


def test_normalizar_sigla_none_with_qty():
    path = _make_workbook([
        ['FUNÇÃO', 'SIGLA', 'CENTRAL'],
        ['ELETRICISTA I', None, 3],
    ])
    try:
        normalized, _, _, warnings = carregar_e_normalizar(path)
    finally:
        os.unlink(path)

    assert normalized == []
    assert any(w['tipo'] == ERRO_SIGLA for w in warnings)


def test_normalizar_two_functions():
    path = _make_workbook([
        ['SIGLA', 'CENTRAL', 'BREAKDOWN PE1', 'Atual'],
        ['ELET-I',  5, 1, 6],
        ['ELET-II', 4, 1, 5],
    ])
    try:
        normalized, raw_sums, atual, warnings = carregar_e_normalizar(path)
    finally:
        os.unlink(path)

    siglas = {r['funcao'] for r in normalized}
    assert siglas == {'ELET-I', 'ELET-II'}
    assert raw_sums['ELET-I'] == 6
    assert raw_sums['ELET-II'] == 5
    assert not any(w['tipo'] in (ERRO_SIGLA, ERRO_TOTAL) for w in warnings)


# ---------------------------------------------------------------------------
# validar
# ---------------------------------------------------------------------------

def test_validar_total_match():
    normalized = [{'funcao': 'ELET-I', 'md_cobranca': 'CENTRAL', 'area': None, 'quantidade': 5}]
    result = validar_distribuicao_cobranca(normalized, {'ELET-I': 5.0}, {})
    assert not any(i['tipo'] == ERRO_TOTAL for i in result)


def test_validar_total_mismatch():
    normalized = [{'funcao': 'ELET-I', 'md_cobranca': 'CENTRAL', 'area': None, 'quantidade': 5}]
    result = validar_distribuicao_cobranca(normalized, {'ELET-I': 7.0}, {})
    assert any(i['tipo'] == ERRO_TOTAL for i in result)


def test_validar_discrepancia_atual():
    normalized = [{'funcao': 'ELET-I', 'md_cobranca': 'CENTRAL', 'area': None, 'quantidade': 5}]
    result = validar_distribuicao_cobranca(normalized, {'ELET-I': 5.0}, {'ELET-I': 8.0})
    assert any(i['tipo'] == AVISO_DISCREPANCIA_ATUAL for i in result)


def test_validar_no_discrepancia_quando_atual_ausente():
    normalized = [{'funcao': 'ELET-I', 'md_cobranca': 'CENTRAL', 'area': None, 'quantidade': 5}]
    result = validar_distribuicao_cobranca(normalized, {'ELET-I': 5.0}, {})
    assert not any(i['tipo'] == AVISO_DISCREPANCIA_ATUAL for i in result)
