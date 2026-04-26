"""Contract guard de app.domain.ferias.gerar_updates_ferias.

Pinniza invariantes estruturais permanentes — distinto da cobertura
per-rule em test_ferias_core.py / test_ferias_rules.py / test_ferias_edge_cases.py.

Cobre:
  - Tipos de retorno: (list[Update], list[Inconsistencia]).
  - Todo Update produzido tem tipo='ferias', sobrescrever_obs=True,
    row não-nulo, observacao não-vazia.
  - Toda Inconsistencia tem origem='ferias'.
  - col_map sem chave obrigatória → RuntimeError (boundary contract).
  - Idempotência: rodar duas vezes com mesma entrada produz output igual.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.domain import ferias
from app.domain.core import Inconsistencia, Update
from tests.fixtures.ferias_factories import (
    build_base_cobranca,
    build_col_map,
    build_col_map_sem,
    build_dado_ferias_aprovado_1,
    build_dado_ferias_periodo_invalido,
    build_md_cobranca_index,
    build_sg_funcao_index,
    mes_referencia_padrao,
)


def _executar_misto():
    dados = [
        build_dado_ferias_aprovado_1(linha=2, chapa='1.000111',
                                     periodo='01/04/2026 a 02/04/2026'),
        build_dado_ferias_aprovado_1(linha=3, chapa='1.000222',
                                     periodo='10/04/2026 a 10/04/2026'),
        build_dado_ferias_periodo_invalido(linha=4, chapa='1.000333'),
    ]
    medicao = {
        '111': [
            (date(2026, 4, 1), '01/04/2026', [10]),
            (date(2026, 4, 2), '02/04/2026', [11]),
        ],
        '222': [(date(2026, 4, 10), '10/04/2026', [25])],
    }
    md = build_md_cobranca_index({
        ('111', '01/04/2026'): 'ADICIONAL',
        ('111', '02/04/2026'): 'ADICIONAL',
        ('222', '10/04/2026'): 'CENTRAL',
    })
    sg = build_sg_funcao_index({
        ('111', '01/04/2026'): 'X',
        ('111', '02/04/2026'): 'X',
        ('222', '10/04/2026'): 'AJUD-CIVIL',
    })
    base = build_base_cobranca({'AJUD-CIVIL': 'FÉRIAS S/ DESC'})
    return ferias.gerar_updates_ferias(
        dados, base, medicao, md, sg,
        mes_referencia_padrao(), build_col_map(),
    )


def test_retorno_eh_tupla_de_listas():
    out = _executar_misto()
    assert isinstance(out, tuple) and len(out) == 2
    atus, incs = out
    assert isinstance(atus, list)
    assert isinstance(incs, list)


def test_todo_update_tem_invariantes_estruturais():
    atus, _ = _executar_misto()
    assert atus, "cenário misto deveria produzir pelo menos 1 update"
    for u in atus:
        assert isinstance(u, Update)
        assert u.tipo == 'ferias'
        assert u.sobrescrever_obs is True
        assert u.row is not None and u.row > 0
        assert u.observacao and isinstance(u.observacao, str)
        assert u.observacao.strip() != ''


def test_toda_inconsistencia_tem_origem_ferias():
    _, incs = _executar_misto()
    assert incs, "cenário misto deveria produzir pelo menos 1 inconsistência"
    for i in incs:
        assert isinstance(i, Inconsistencia)
        assert i.origem == 'ferias'


@pytest.mark.parametrize('chave_omissa', ['situacao', 'md_cobranca', 'sg_funcao'])
def test_col_map_incompleto_levanta_runtime_error(chave_omissa):
    with pytest.raises(RuntimeError, match=chave_omissa):
        ferias.gerar_updates_ferias(
            [], build_base_cobranca(), {}, {}, {},
            mes_referencia_padrao(), build_col_map_sem(chave_omissa),
        )


def test_idempotencia_duas_execucoes_produzem_output_igual():
    out1 = _executar_misto()
    out2 = _executar_misto()
    assert out1 == out2
