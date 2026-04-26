"""Equivalencia legacy vs novo (domain/application).

Cada cenario roda o legacy e o novo com a mesma entrada e compara
estruturalmente via dataclass __eq__. Suite descartavel — deletada
no Step 5 quando o legacy for removido.
"""

from __future__ import annotations

import re
from dataclasses import asdict

import pytest

from app import validar_distribuicao as legacy
from app.application.services import validacao_distribuicao as new_service
from app.domain import distribuicao as new_domain
from tests.fixtures.distribuicao_factories import (
    build_bd_record,
    build_medicao_record,
    build_registros,
)

TS_RE = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}')


CENARIOS = {
    'caso_feliz': (
        [build_bd_record(quantidade=1.0)],
        [build_medicao_record(pct_cobranca=1.0)],
    ),
    'linha_ausente': (
        [build_bd_record(funcao='OP', md_cobranca='CENTRAL', quantidade=1.0)],
        [build_medicao_record(sg_funcao='OP', md_cobranca='ADM-B', pct_cobranca=1.0)],
    ),
    'insuficiencia': (
        [build_bd_record(quantidade=1.0)],
        [build_medicao_record(pct_cobranca=0.4)],
    ),
    'excesso': (
        [build_bd_record(quantidade=1.0)],
        [build_medicao_record(pct_cobranca=1.5)],
    ),
    'multi_data': (
        [build_bd_record(quantidade=1.0)],
        [
            build_medicao_record(data='01/04/2026', pct_cobranca=1.0),
            build_medicao_record(data='02/04/2026', pct_cobranca=0.5),
            build_medicao_record(data='03/04/2026', pct_cobranca=1.5),
        ],
    ),
    'precision_edge': (
        [build_bd_record(quantidade=0.1 + 0.2)],
        [build_medicao_record(pct_cobranca=0.3)],
    ),
    'agregacao_por_area': (
        [
            build_bd_record(area='PE-1', quantidade=0.5),
            build_bd_record(area='PE-2', quantidade=0.5),
        ],
        [build_medicao_record(pct_cobranca=0.4)],
    ),
    'funcao_sem_match_no_bd': (
        [build_bd_record(funcao='A', quantidade=1.0)],
        [build_medicao_record(sg_funcao='B', pct_cobranca=1.0)],
    ),
    'multi_funcao_multi_md': (
        [
            build_bd_record(funcao='OP1', md_cobranca='CENTRAL', quantidade=1.0),
            build_bd_record(funcao='OP1', md_cobranca='ADM-B',   quantidade=0.5),
            build_bd_record(funcao='OP2', md_cobranca='HD',      quantidade=0.7),
        ],
        [
            build_medicao_record(sg_funcao='OP1', md_cobranca='CENTRAL', pct_cobranca=1.0),
            build_medicao_record(sg_funcao='OP1', md_cobranca='ADM-B',   pct_cobranca=0.3),
            build_medicao_record(sg_funcao='OP2', md_cobranca='HD',      pct_cobranca=0.7),
        ],
    ),
}


@pytest.mark.parametrize('nome', list(CENARIOS))
def test_validar_aderencia_equivalente(nome):
    bd, medicao = CENARIOS[nome]
    legacy_out = [asdict(x) for x in legacy.validar_aderencia_distribuicao(bd, medicao)]
    new_out    = [asdict(x) for x in new_domain.validar_aderencia_distribuicao(bd, medicao)]
    assert legacy_out == new_out


@pytest.mark.parametrize('nome', list(CENARIOS))
def test_validar_para_dominio_equivalente(nome):
    bd, medicao = CENARIOS[nome]
    assert legacy.validar_para_dominio(bd, medicao) == \
           new_service.validar_para_dominio(bd, medicao)


@pytest.mark.parametrize('nome', list(CENARIOS))
def test_gerar_relatorio_byte_equivalente(nome):
    bd, medicao = CENARIOS[nome]
    incs_legacy = legacy.validar_aderencia_distribuicao(bd, medicao)
    incs_new    = new_domain.validar_aderencia_distribuicao(bd, medicao)
    registros = build_registros()
    txt_legacy = legacy.gerar_relatorio(incs_legacy, registros, 1, 1, [])
    txt_new    = new_domain.gerar_relatorio(incs_new,   registros, 1, 1, [])
    assert TS_RE.sub('TS', txt_legacy) == TS_RE.sub('TS', txt_new)
