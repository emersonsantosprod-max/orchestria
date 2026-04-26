"""
Characterization snapshot of `app.distribuicao_contratual` (legacy flat module).

Disposable: deleted at Step 6 of the layered-architecture migration once the
legacy module is decommissioned. Captures today's `carregar_e_normalizar` and
`validar_distribuicao_cobranca` output for a fixture covering the main code
paths (full header set, decimal qty, Atual divergence, zero rows, missing
sigla with qty, unknown header).
"""

from __future__ import annotations

import openpyxl
import pytest

from app.distribuicao_contratual import (
    carregar_e_normalizar,
    validar_distribuicao_cobranca,
)

_FIXTURE_ROWS = [
    [
        'TP MO', 'ÁREA', 'FUNÇÃO', 'SIGLA',
        'CENTRAL', 'ADM-B',
        'BREAKDOWN PE1', 'BREAKDOWN PVC',
        'HD PVC', 'CV UA', 'ANALITICA',
        'COLUNA_ESTRANHA',
        'Atual', 'OBSERVAÇÕES',
    ],
    ['MOD', 'ELÉTRICA', 'ELETRICISTA I',  'ELET-I',  5, 1, 2, 1, None, None, None, None, 9, ''],
    ['MOD', 'MECÂNICA', 'MECANICO II',    'MEC-II',  3, 0, 0, 0, 1.5,  0,    None, None, 5, ''],
    ['MOD', 'INSTRUM',  'INSTRUMENTISTA', 'INST-I',  0, 0, 0, 0, 0,    2,    1,    None, 4, ''],
    ['MOD', 'GERAL',    'AJUDANTE',       None,      0, 0, 0, 0, 0,    0,    1,    None, 0, ''],
]


@pytest.fixture(scope='module')
def fixture_entrada(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp('distribuicao_contratual') / 'entrada.xlsx'
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in _FIXTURE_ROWS:
        ws.append(row)
    wb.save(path)
    wb.close()
    return str(path)


def _key_normalized(r: dict) -> tuple:
    return (r['funcao'], r['md_cobranca'], r['area'] or '')


def _key_warning(w: dict) -> tuple:
    return (w.get('tipo', ''), w.get('funcao', ''), w.get('coluna', ''),
            w.get('md_cobranca', ''), w.get('area') or '')


def test_carregar_e_normalizar_snapshot(fixture_entrada):
    normalized, raw_sums, atual, warnings = carregar_e_normalizar(fixture_entrada)

    normalized_sorted = sorted(normalized, key=_key_normalized)
    expected_normalized = [
        {'funcao': 'ELET-I',  'md_cobranca': 'ADM-B',     'area': None,  'quantidade': 1},
        {'funcao': 'ELET-I',  'md_cobranca': 'BREAKDOWN', 'area': 'PE-1','quantidade': 2},
        {'funcao': 'ELET-I',  'md_cobranca': 'BREAKDOWN', 'area': 'PVC', 'quantidade': 1},
        {'funcao': 'ELET-I',  'md_cobranca': 'CENTRAL',   'area': None,  'quantidade': 5},
        {'funcao': 'INST-I',  'md_cobranca': 'BREAKDOWN', 'area': 'ANALITICA', 'quantidade': 1},
        {'funcao': 'INST-I',  'md_cobranca': 'CV',        'area': 'UA',  'quantidade': 2},
        {'funcao': 'MEC-II',  'md_cobranca': 'CENTRAL',   'area': None,  'quantidade': 3},
        {'funcao': 'MEC-II',  'md_cobranca': 'HD',        'area': 'PVC', 'quantidade': 1.5},
    ]
    assert normalized_sorted == sorted(expected_normalized, key=_key_normalized)

    assert dict(sorted(raw_sums.items())) == {
        'ELET-I': 9.0,
        'INST-I': 3.0,
        'MEC-II': 4.5,
    }

    assert dict(sorted(atual.items())) == {
        'ELET-I': 9.0,
        'INST-I': 4.0,
        'MEC-II': 5.0,
    }

    warning_types = sorted(w['tipo'] for w in warnings)
    assert warning_types == [
        'AVISO_COLUNA_DESCONHECIDA',
        'AVISO_DECIMAL',
        'ERRO_SIGLA',
    ]


def test_validar_distribuicao_cobranca_snapshot(fixture_entrada):
    normalized, raw_sums, atual, _ = carregar_e_normalizar(fixture_entrada)
    incons = validar_distribuicao_cobranca(normalized, raw_sums, atual)

    types = sorted(i['tipo'] for i in incons)
    assert types == ['AVISO_DISCREPANCIA_ATUAL', 'AVISO_DISCREPANCIA_ATUAL']

    by_sigla = {i['funcao']: i for i in incons}
    assert set(by_sigla.keys()) == {'INST-I', 'MEC-II'}
    assert by_sigla['INST-I']['normalized_sum'] == 3.0
    assert by_sigla['INST-I']['atual'] == 4.0
    assert by_sigla['MEC-II']['normalized_sum'] == 4.5
    assert by_sigla['MEC-II']['atual'] == 5.0
