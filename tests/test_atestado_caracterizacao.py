"""Caracterização comportamental do legacy app.atestado.

Congela o comportamento atual como oráculo executável (comportamental,
não estrutural). Cobre ramificações conhecidas + determinismo.

Regras (CLAUDE.md):
  - ordem da lista de saída NÃO é contrato — comparações futuras
    (Step 3) normalizam antes de assert.
  - este arquivo registra ordem observada apenas como detecção de
    regressão interna no legacy, não como compromisso público.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app import atestado as legacy_atestado


def _normalizar_updates(updates):
    return sorted(
        [
            (u.tipo, u.matricula, u.data, u.observacao, u.situacao,
             u.sobrescrever_obs, u.row, u.desconto_min)
            for u in updates
        ],
        key=lambda t: (t[1], t[2], t[0]),
    )


def _normalizar_inconsistencias(incs):
    return sorted(
        [(i.origem, i.matricula, i.data, i.erro, i.linha) for i in incs],
        key=lambda t: (t[0], t[1] or '', t[2] or '', t[3] or '', str(t[4])),
    )


@pytest.mark.parametrize(
    'dados, esperado_updates_norm, esperado_incs_norm',
    [
        (
            [],
            [],
            [],
        ),
        (
            [{'linha': 2, 'matricula': '111', 'inicio': datetime(2026, 3, 18),
              'fim': datetime(2026, 3, 18)}],
            [('atestado', '111', '18/03/2026', 'ATESTADO MÉDICO',
              'AUSENTE', True, None, None)],
            [],
        ),
        (
            [{'linha': 2, 'matricula': '111', 'inicio': datetime(2026, 3, 18),
              'fim': datetime(2026, 3, 20)}],
            [
                ('atestado', '111', '18/03/2026', 'ATESTADO MÉDICO',
                 'AUSENTE', True, None, None),
                ('atestado', '111', '19/03/2026', 'ATESTADO MÉDICO',
                 'AUSENTE', True, None, None),
                ('atestado', '111', '20/03/2026', 'ATESTADO MÉDICO',
                 'AUSENTE', True, None, None),
            ],
            [],
        ),
        (
            [{'linha': 2, 'matricula': '111', 'inicio': datetime(2026, 3, 20),
              'fim': datetime(2026, 3, 18)}],
            [],
            [],
        ),
        (
            [{'linha': 2, 'matricula': '111', 'inicio': None,
              'fim': datetime(2026, 3, 18)}],
            [],
            [],
        ),
        (
            [{'linha': 2, 'matricula': '  00111  ', 'inicio': datetime(2026, 3, 18),
              'fim': datetime(2026, 3, 18)}],
            None,
            [],
        ),
        (
            [{'linha': 2, 'matricula': '111', 'inicio': datetime(2026, 3, 31),
              'fim': datetime(2026, 4, 2)}],
            [
                ('atestado', '111', '01/04/2026', 'ATESTADO MÉDICO',
                 'AUSENTE', True, None, None),
                ('atestado', '111', '02/04/2026', 'ATESTADO MÉDICO',
                 'AUSENTE', True, None, None),
                ('atestado', '111', '31/03/2026', 'ATESTADO MÉDICO',
                 'AUSENTE', True, None, None),
            ],
            [],
        ),
        (
            [
                {'linha': 2, 'matricula': '111', 'inicio': datetime(2026, 3, 18),
                 'fim': datetime(2026, 3, 18)},
                {'linha': 3, 'matricula': '111', 'inicio': datetime(2026, 3, 18),
                 'fim': datetime(2026, 3, 18)},
            ],
            [
                ('atestado', '111', '18/03/2026', 'ATESTADO MÉDICO',
                 'AUSENTE', True, None, None),
                ('atestado', '111', '18/03/2026', 'ATESTADO MÉDICO',
                 'AUSENTE', True, None, None),
            ],
            [],
        ),
    ],
    ids=[
        'lista_vazia',
        'um_dia',
        'tres_dias',
        'inicio_maior_que_fim',
        'data_invalida_skip',
        'matricula_normalizada',
        'virada_de_mes',
        'duplicatas_preservadas',
    ],
)
def test_caracterizacao_legacy(dados, esperado_updates_norm, esperado_incs_norm):
    updates, incs = legacy_atestado.gerar_updates_atestado(dados)

    if esperado_updates_norm is not None:
        assert _normalizar_updates(updates) == esperado_updates_norm

    assert _normalizar_inconsistencias(incs) == esperado_incs_norm


def test_matricula_normalizada_remove_whitespace_e_zeros():
    dados = [{'linha': 2, 'matricula': '  00111  ',
              'inicio': datetime(2026, 3, 18), 'fim': datetime(2026, 3, 18)}]
    updates, _ = legacy_atestado.gerar_updates_atestado(dados)
    assert len(updates) == 1
    assert updates[0].matricula == '111'


def test_determinismo_legacy_mesma_entrada_mesma_saida():
    dados = [
        {'linha': 2, 'matricula': '111', 'inicio': datetime(2026, 3, 18),
         'fim': datetime(2026, 3, 22)},
        {'linha': 3, 'matricula': '222', 'inicio': datetime(2026, 3, 19),
         'fim': datetime(2026, 3, 19)},
        {'linha': 4, 'matricula': '111', 'inicio': datetime(2026, 3, 20),
         'fim': datetime(2026, 3, 21)},
    ]
    execucoes = [legacy_atestado.gerar_updates_atestado(dados) for _ in range(5)]

    referencia_norm = (
        _normalizar_updates(execucoes[0][0]),
        _normalizar_inconsistencias(execucoes[0][1]),
    )
    for ups, incs in execucoes[1:]:
        assert (_normalizar_updates(ups),
                _normalizar_inconsistencias(incs)) == referencia_norm


def test_estabilidade_de_ordem_observada_legacy():
    """Observação (não contrato): legacy gera updates em ordem
    cronológica dentro de cada item de entrada e preserva ordem dos
    itens de entrada. Útil para detectar regressões internas no legacy
    enquanto ele coexiste com o domain.
    """
    dados = [
        {'linha': 2, 'matricula': '222', 'inicio': datetime(2026, 3, 19),
         'fim': datetime(2026, 3, 19)},
        {'linha': 3, 'matricula': '111', 'inicio': datetime(2026, 3, 18),
         'fim': datetime(2026, 3, 20)},
    ]
    updates, _ = legacy_atestado.gerar_updates_atestado(dados)
    ordem_observada = [(u.matricula, u.data) for u in updates]
    assert ordem_observada == [
        ('222', '19/03/2026'),
        ('111', '18/03/2026'),
        ('111', '19/03/2026'),
        ('111', '20/03/2026'),
    ]
