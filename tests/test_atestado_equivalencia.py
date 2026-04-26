"""Equivalência funcional entre legacy (app.atestado) e domain
(app.domain.atestado).

Comparação comportamental, não estrutural:
  - dataclasses convertidos para tuplas de valores primitivos
  - listas ordenadas antes de comparar (ordem não é contrato)
  - inputs reusados da Step 2 + paramétrico estendido

Esta suíte deixa de existir após Step 5 (decommission do legacy):
sem oráculo paralelo, comparação consigo mesmo é tautologia.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta

import pytest

from app import atestado as legacy_atestado
from app.domain import atestado as domain_atestado


def _norm_updates(updates):
    return sorted(
        [tuple(sorted(dataclasses.asdict(u).items())) for u in updates]
    )


def _norm_inconsistencias(incs):
    return sorted(
        [tuple(sorted(dataclasses.asdict(i).items())) for i in incs]
    )


def _equivalente(dados):
    leg_u, leg_i = legacy_atestado.gerar_updates_atestado(dados)
    dom_u, dom_i = domain_atestado.gerar_updates_atestado(dados)
    assert _norm_updates(leg_u) == _norm_updates(dom_u)
    assert _norm_inconsistencias(leg_i) == _norm_inconsistencias(dom_i)


@pytest.mark.parametrize(
    'dados',
    [
        [],
        [{'linha': 2, 'matricula': '111',
          'inicio': datetime(2026, 3, 18), 'fim': datetime(2026, 3, 18)}],
        [{'linha': 2, 'matricula': '111',
          'inicio': datetime(2026, 3, 18), 'fim': datetime(2026, 3, 20)}],
        [{'linha': 2, 'matricula': '111',
          'inicio': datetime(2026, 3, 20), 'fim': datetime(2026, 3, 18)}],
        [{'linha': 2, 'matricula': '111',
          'inicio': None, 'fim': datetime(2026, 3, 18)}],
        [{'linha': 2, 'matricula': '111',
          'inicio': datetime(2026, 3, 18), 'fim': None}],
        [{'linha': 2, 'matricula': '  00111  ',
          'inicio': datetime(2026, 3, 18), 'fim': datetime(2026, 3, 18)}],
        [{'linha': 2, 'matricula': '1.095585',
          'inicio': datetime(2026, 3, 18), 'fim': datetime(2026, 3, 18)}],
        [{'linha': 2, 'matricula': '111',
          'inicio': datetime(2026, 3, 31), 'fim': datetime(2026, 4, 2)}],
        [{'linha': 2, 'matricula': '111',
          'inicio': datetime(2026, 12, 30), 'fim': datetime(2027, 1, 2)}],
        [
            {'linha': 2, 'matricula': '111',
             'inicio': datetime(2026, 3, 18), 'fim': datetime(2026, 3, 18)},
            {'linha': 3, 'matricula': '111',
             'inicio': datetime(2026, 3, 18), 'fim': datetime(2026, 3, 18)},
        ],
        [
            {'linha': 2, 'matricula': '222',
             'inicio': datetime(2026, 3, 19), 'fim': datetime(2026, 3, 19)},
            {'linha': 3, 'matricula': '111',
             'inicio': datetime(2026, 3, 18), 'fim': datetime(2026, 3, 20)},
        ],
    ],
    ids=[
        'vazio',
        'um_dia',
        'tres_dias',
        'inicio_maior_que_fim',
        'inicio_none',
        'fim_none',
        'matricula_zeros',
        'matricula_com_ponto',
        'virada_de_mes',
        'virada_de_ano',
        'duplicatas',
        'multi_matricula',
    ],
)
def test_equivalencia_legacy_domain(dados):
    _equivalente(dados)


@pytest.mark.parametrize('dias', [0, 1, 5, 30, 90])
@pytest.mark.parametrize('matricula', ['1', '999', '012345', '  77  ',
                                       '1.095585'])
def test_equivalencia_intervalos_e_matriculas(dias, matricula):
    inicio = datetime(2026, 3, 1)
    dados = [{
        'linha': 2,
        'matricula': matricula,
        'inicio': inicio,
        'fim': inicio + timedelta(days=dias),
    }]
    _equivalente(dados)


def test_equivalencia_lote_grande():
    inicio = datetime(2026, 1, 1)
    dados = [
        {'linha': i + 2,
         'matricula': str(100 + (i % 7)),
         'inicio': inicio + timedelta(days=i),
         'fim': inicio + timedelta(days=i + (i % 4))}
        for i in range(50)
    ]
    _equivalente(dados)
