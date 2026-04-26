"""Per-rule unit tests for `app.domain.distribuicao_contratual` (pure)."""

from __future__ import annotations

from app.domain.distribuicao_contratual import (
    AVISO_COLUNA_DESCONHECIDA,
    AVISO_DECIMAL,
    AVISO_DISCREPANCIA_ATUAL,
    ERRO_SIGLA,
    ERRO_TOTAL,
    localizar_colunas_chave,
    normalizar_linhas,
    normalize_area,
    parse_distribuicao_cols,
    validar_distribuicao_cobranca,
)


def test_normalize_area_pe():
    assert normalize_area('PE1') == 'PE-1'
    assert normalize_area('PE2') == 'PE-2'
    assert normalize_area('PE3') == 'PE-3'


def test_normalize_area_passthrough():
    for raw in ('PVC', 'UO', 'UA', 'IESE', 'TEGAL', 'ANALITICA'):
        assert normalize_area(raw) == raw


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
    assert col_map[h.index('CENTRAL')]       == ('CENTRAL', None)
    assert col_map[h.index('ADM-B')]         == ('ADM-B', None)
    assert col_map[h.index('ANALITICA')]     == ('BREAKDOWN', 'ANALITICA')
    assert col_map[h.index('BREAKDOWN PE1')] == ('BREAKDOWN', 'PE-1')
    assert col_map[h.index('HD PVC')]        == ('HD', 'PVC')
    assert col_map[h.index('CV UO')]         == ('CV', 'UO')
    assert not warnings


def test_parse_distribuicao_cols_skip_headers_excluidos():
    col_map, _ = parse_distribuicao_cols(_FULL_HEADERS)
    for name in ('TP MO', 'ÁREA', 'FUNÇÃO', 'SIGLA', 'INSPEÇÃO', 'Atual', 'OBSERVAÇÕES'):
        assert _FULL_HEADERS.index(name) not in col_map


def test_parse_distribuicao_cols_unknown_header_emite_aviso():
    headers = ('SIGLA', 'CENTRAL', 'COLUNA_ESTRANHA')
    col_map, warnings = parse_distribuicao_cols(headers)
    assert 2 not in col_map
    assert any(w['tipo'] == AVISO_COLUNA_DESCONHECIDA for w in warnings)


def test_localizar_colunas_chave_basico():
    headers = ('TP MO', 'FUNÇÃO', 'SIGLA', 'CENTRAL', 'Atual')
    sigla_col, funcao_col, atual_col = localizar_colunas_chave(headers)
    assert (sigla_col, funcao_col, atual_col) == (2, 1, 4)


def test_localizar_colunas_chave_funcao_e_atual_opcionais():
    headers = ('SIGLA', 'CENTRAL')
    sigla_col, funcao_col, atual_col = localizar_colunas_chave(headers)
    assert (sigla_col, funcao_col, atual_col) == (0, None, None)


def test_localizar_colunas_chave_sem_sigla_levanta():
    import pytest
    with pytest.raises(ValueError, match='SIGLA'):
        localizar_colunas_chave(('FUNÇÃO', 'CENTRAL'))


def test_normalizar_linhas_amostra():
    headers = ('TP MO', 'ÁREA', 'FUNÇÃO', 'SIGLA',
               'CENTRAL', 'BREAKDOWN PVC', 'BREAKDOWN UA', 'Atual')
    col_map, _ = parse_distribuicao_cols(headers)
    sigla_col, funcao_col, atual_col = localizar_colunas_chave(headers)
    rows = [('MOD', 'ELÉTRICA', 'ELETRICISTA I', 'ELET-I', 5, 2, 1, 8)]
    normalized, raw_sums, atual, warnings = normalizar_linhas(
        rows, col_map, sigla_col, funcao_col, atual_col)

    by_key = {(r['md_cobranca'], r['area']): r['quantidade'] for r in normalized}
    assert by_key == {('CENTRAL', None): 5, ('BREAKDOWN', 'PVC'): 2, ('BREAKDOWN', 'UA'): 1}
    assert all(r['funcao'] == 'ELET-I' for r in normalized)
    assert raw_sums['ELET-I'] == 8
    assert atual['ELET-I'] == 8.0
    assert not any(w['tipo'] in (ERRO_SIGLA, ERRO_TOTAL) for w in warnings)


def test_normalizar_linhas_skip_zero():
    headers = ('SIGLA', 'CENTRAL', 'BREAKDOWN PE1')
    col_map, _ = parse_distribuicao_cols(headers)
    sigla_col, _, _ = localizar_colunas_chave(headers)
    rows = [('ELET-I', 0, None)]
    normalized, raw_sums, _, _ = normalizar_linhas(rows, col_map, sigla_col, None, None)
    assert normalized == []
    assert raw_sums.get('ELET-I', 0) == 0


def test_normalizar_linhas_aviso_decimal():
    headers = ('SIGLA', 'CENTRAL')
    col_map, _ = parse_distribuicao_cols(headers)
    sigla_col, _, _ = localizar_colunas_chave(headers)
    rows = [('ELET-I', 1.5)]
    normalized, _, _, warnings = normalizar_linhas(rows, col_map, sigla_col, None, None)
    assert len(normalized) == 1
    assert normalized[0]['quantidade'] == 1.5
    assert any(w['tipo'] == AVISO_DECIMAL for w in warnings)


def test_normalizar_linhas_sigla_none_com_qty_emite_erro():
    headers = ('FUNÇÃO', 'SIGLA', 'CENTRAL')
    col_map, _ = parse_distribuicao_cols(headers)
    sigla_col, funcao_col, _ = localizar_colunas_chave(headers)
    rows = [('ELETRICISTA I', None, 3)]
    normalized, _, _, warnings = normalizar_linhas(rows, col_map, sigla_col, funcao_col, None)
    assert normalized == []
    assert any(w['tipo'] == ERRO_SIGLA for w in warnings)


def test_normalizar_linhas_ignora_segunda_linha_de_header():
    headers = ('SIGLA', 'CENTRAL')
    col_map, _ = parse_distribuicao_cols(headers)
    sigla_col, _, _ = localizar_colunas_chave(headers)
    rows = [('ELET-I', 5), ('SIGLA', 'CENTRAL'), ('ELET-II', 3)]
    normalized, raw_sums, _, _ = normalizar_linhas(rows, col_map, sigla_col, None, None)
    assert {r['funcao'] for r in normalized} == {'ELET-I', 'ELET-II'}
    assert raw_sums == {'ELET-I': 5, 'ELET-II': 3}


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
