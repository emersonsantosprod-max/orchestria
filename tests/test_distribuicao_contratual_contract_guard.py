"""
Contract guard for `app.domain.distribuicao_contratual`.

Structural invariants only — no fixture file, no legacy comparison, no
reuse of integration/equivalence scenarios. All inputs constructed inline.
Persists in steady state.
"""

from __future__ import annotations

from app.domain.distribuicao_contratual import (
    AVISO_COLUNA_DESCONHECIDA,
    AVISO_COLUNA_DUPLICADA,
    AVISO_DECIMAL,
    AVISO_DISCREPANCIA_ATUAL,
    AVISO_HEADER_DUPLICADO,
    AVISO_SIGLA_DUPLICADA,
    AVISO_VALOR_NAO_NUMERICO,
    ERRO_SIGLA,
    ERRO_TOTAL,
    normalizar_linhas,
    normalize_area,
    parse_distribuicao_cols,
    validar_distribuicao_cobranca,
)

_PUBLISHED = frozenset({
    ERRO_SIGLA, ERRO_TOTAL, AVISO_DECIMAL, AVISO_SIGLA_DUPLICADA,
    AVISO_COLUNA_DESCONHECIDA, AVISO_COLUNA_DUPLICADA,
    AVISO_VALOR_NAO_NUMERICO, AVISO_DISCREPANCIA_ATUAL,
    AVISO_HEADER_DUPLICADO,
})


def test_parse_distribuicao_cols_return_type():
    col_map, warnings = parse_distribuicao_cols(('SIGLA', 'CENTRAL'))
    assert isinstance(col_map, dict)
    assert isinstance(warnings, list)


def test_normalizar_linhas_return_type():
    headers = ('SIGLA', 'CENTRAL')
    col_map, _ = parse_distribuicao_cols(headers)
    out = normalizar_linhas([], col_map, 0, None, None)
    assert isinstance(out, tuple) and len(out) == 4
    normalized, raw_sums, atual, warnings = out
    assert isinstance(normalized, list)
    assert isinstance(raw_sums, dict)
    assert isinstance(atual, dict)
    assert isinstance(warnings, list)


def test_validar_return_type():
    out = validar_distribuicao_cobranca([], {}, {})
    assert isinstance(out, list)


def test_warnings_carregam_apenas_tipos_publicados():
    headers = ('SIGLA', 'CENTRAL', 'COLUNA_X', 'COLUNA_X')
    _, w_cols = parse_distribuicao_cols(headers)
    assert all(w['tipo'] in _PUBLISHED for w in w_cols)

    rows = [('ELET-I', 1.5), ('ELET-I', 2)]
    col_map, _ = parse_distribuicao_cols(('SIGLA', 'CENTRAL'))
    _, _, _, w_norm = normalizar_linhas(rows, col_map, 0, None, None)
    assert all(w['tipo'] in _PUBLISHED for w in w_norm)


def test_normalizado_tem_chaves_obrigatorias():
    headers = ('SIGLA', 'CENTRAL', 'BREAKDOWN PVC')
    col_map, _ = parse_distribuicao_cols(headers)
    normalized, _, _, _ = normalizar_linhas(
        [('ELET-I', 5, 2)], col_map, 0, None, None)
    for r in normalized:
        assert set(r.keys()) == {'funcao', 'md_cobranca', 'area', 'quantidade'}


def test_determinismo_normalizar_linhas():
    headers = ('SIGLA', 'CENTRAL', 'BREAKDOWN PVC')
    col_map, _ = parse_distribuicao_cols(headers)
    rows = [('ELET-I', 5, 2), ('MEC-II', 3, 1)]
    a = normalizar_linhas(rows, col_map, 0, None, None)
    b = normalizar_linhas(rows, col_map, 0, None, None)
    assert a == b


def test_determinismo_validar():
    normalized = [
        {'funcao': 'ELET-I', 'md_cobranca': 'CENTRAL', 'area': None, 'quantidade': 5},
    ]
    a = validar_distribuicao_cobranca(normalized, {'ELET-I': 5.0}, {'ELET-I': 7.0})
    b = validar_distribuicao_cobranca(normalized, {'ELET-I': 5.0}, {'ELET-I': 7.0})
    assert a == b


def test_normalize_area_pe_mapping():
    assert normalize_area('PE1') == 'PE-1'
    assert normalize_area('PE2') == 'PE-2'
    assert normalize_area('PE3') == 'PE-3'


def test_zero_quantidade_nao_gera_registro_normalizado():
    headers = ('SIGLA', 'CENTRAL')
    col_map, _ = parse_distribuicao_cols(headers)
    normalized, raw_sums, _, _ = normalizar_linhas(
        [('ELET-I', 0)], col_map, 0, None, None)
    assert normalized == []
    assert raw_sums.get('ELET-I', 0) == 0


def test_decimal_emite_aviso():
    headers = ('SIGLA', 'CENTRAL')
    col_map, _ = parse_distribuicao_cols(headers)
    _, _, _, w = normalizar_linhas([('ELET-I', 1.5)], col_map, 0, None, None)
    assert any(x['tipo'] == AVISO_DECIMAL for x in w)


def test_sigla_ausente_com_qty_emite_erro():
    headers = ('SIGLA', 'CENTRAL')
    col_map, _ = parse_distribuicao_cols(headers)
    _, _, _, w = normalizar_linhas([(None, 3)], col_map, 0, None, None)
    assert any(x['tipo'] == ERRO_SIGLA for x in w)


def test_total_match_sem_erro_total():
    normalized = [{'funcao': 'X', 'md_cobranca': 'CENTRAL', 'area': None, 'quantidade': 5}]
    inc = validar_distribuicao_cobranca(normalized, {'X': 5.0}, {})
    assert not any(i['tipo'] == ERRO_TOTAL for i in inc)


def test_total_mismatch_emite_erro_total():
    normalized = [{'funcao': 'X', 'md_cobranca': 'CENTRAL', 'area': None, 'quantidade': 5}]
    inc = validar_distribuicao_cobranca(normalized, {'X': 7.0}, {})
    assert any(i['tipo'] == ERRO_TOTAL for i in inc)


def test_parse_headers_vazio_nao_levanta():
    col_map, warnings = parse_distribuicao_cols(())
    assert col_map == {}
    assert isinstance(warnings, list)


def test_parse_headers_com_duplicado_emite_aviso_coluna_duplicada():
    headers = ('SIGLA', 'CENTRAL', 'CENTRAL')
    _, warnings = parse_distribuicao_cols(headers)
    assert any(w['tipo'] == AVISO_COLUNA_DUPLICADA for w in warnings)


def test_normalizar_linhas_vazio_retorna_identidade():
    col_map, _ = parse_distribuicao_cols(('SIGLA', 'CENTRAL'))
    assert normalizar_linhas([], col_map, 0, None, None) == ([], {}, {}, [])


def test_validar_vazio_retorna_lista_vazia():
    assert validar_distribuicao_cobranca([], {}, {}) == []


def test_parse_distribuicao_cols_preserva_ordem_headers():
    headers = (
        'SIGLA', 'CENTRAL', 'BREAKDOWN PE1', 'ADM-B',
        'HD PVC', 'CV UA', 'ANALITICA',
    )
    col_map, _ = parse_distribuicao_cols(headers)
    keys = list(col_map.keys())
    assert keys == sorted(keys)


def test_parse_distribuicao_cols_determinismo():
    headers = ('SIGLA', 'CENTRAL', 'BREAKDOWN PE1', 'HD PVC')
    a_map, a_warn = parse_distribuicao_cols(headers)
    b_map, b_warn = parse_distribuicao_cols(headers)
    assert a_map == b_map
    assert list(a_map.items()) == list(b_map.items())
    assert a_warn == b_warn


def test_normalizar_linhas_ordem_e_warnings_estaveis():
    headers = ('SIGLA', 'CENTRAL', 'BREAKDOWN PVC')
    col_map, _ = parse_distribuicao_cols(headers)
    rows = [('ELET-I', 5, 2.5), ('MEC-II', 3, 1)]
    n_a, raw_a, atu_a, w_a = normalizar_linhas(rows, col_map, 0, None, None)
    n_b, raw_b, atu_b, w_b = normalizar_linhas(rows, col_map, 0, None, None)
    assert n_a == n_b
    assert list(raw_a.items()) == list(raw_b.items())
    assert atu_a == atu_b
    assert w_a == w_b


def test_aviso_discrepancia_atual_emitido_quando_atual_difere():
    normalized = [{'funcao': 'X', 'md_cobranca': 'CENTRAL', 'area': None, 'quantidade': 5}]
    inc = validar_distribuicao_cobranca(normalized, {'X': 5.0}, {'X': 8.0})
    assert any(i['tipo'] == AVISO_DISCREPANCIA_ATUAL for i in inc)
