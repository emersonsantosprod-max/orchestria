"""Equivalência legacy (app.ferias) ≡ domain (app.domain.ferias).

Cada teste roda o mesmo input nas duas implementações e compara
(updates, inconsistencias) por igualdade estrutural via dataclass __eq__.

Cobre as 4 saídas de _classificar (FERIAS_DIRETO, FERIAS_SD, FERIAS, SKIP)
e os ramos de erro/skip. Disposável: deletado no Step 5.
"""

from __future__ import annotations

from datetime import date

import pytest

from app import ferias as legacy
from app.domain import ferias as dominio
from tests.fixtures.ferias_factories import (
    build_base_cobranca,
    build_col_map,
    build_col_map_sem,
    build_dado_ferias_aprovado_1,
    build_dado_ferias_aprovado_2,
    build_dado_ferias_periodo_invalido,
    build_dado_ferias_sem_aprovacao,
    build_md_cobranca_index,
    build_medicao_index,
    build_sg_funcao_index,
    mes_referencia_padrao,
)


def _comparar(legacy_out, dominio_out):
    atus_l, incs_l = legacy_out
    atus_d, incs_d = dominio_out
    assert atus_l == atus_d, (
        "updates divergem entre legacy e domain"
    )
    assert incs_l == incs_d, (
        "inconsistencias divergem entre legacy e domain"
    )


def _executar(dados, base, medicao, md, sg, mes=None, col=None):
    mes = mes or mes_referencia_padrao()
    col = col or build_col_map()
    return (
        legacy.gerar_updates_ferias(dados, base, medicao, md, sg, mes, col),
        dominio.gerar_updates_ferias(dados, base, medicao, md, sg, mes, col),
    )


def test_eq_lista_vazia():
    _comparar(*_executar([], build_base_cobranca(), {}, {}, {}))


def test_eq_ferias_direto():
    dados = [build_dado_ferias_aprovado_1()]
    medicao = build_medicao_index('111', [(date(2026, 4, 1), '01/04/2026', [10])])
    md = build_md_cobranca_index({('111', '01/04/2026'): 'ADICIONAL'})
    sg = build_sg_funcao_index({('111', '01/04/2026'): 'X'})
    _comparar(*_executar(dados, build_base_cobranca(), medicao, md, sg))


def test_eq_ferias_sd_com_sufixo():
    dados = [build_dado_ferias_aprovado_1()]
    medicao = build_medicao_index('111', [(date(2026, 4, 1), '01/04/2026', [10])])
    md = build_md_cobranca_index({('111', '01/04/2026'): 'CENTRAL'})
    sg = build_sg_funcao_index({('111', '01/04/2026'): 'AJUD-CIVIL'})
    base = build_base_cobranca({'AJUD-CIVIL': 'FÉRIAS S/ DESC'})
    _comparar(*_executar(dados, base, medicao, md, sg))


def test_eq_ferias_lookup_sem_sufixo():
    dados = [build_dado_ferias_aprovado_1()]
    medicao = build_medicao_index('111', [(date(2026, 4, 1), '01/04/2026', [10])])
    md = build_md_cobranca_index({('111', '01/04/2026'): 'CENTRAL'})
    sg = build_sg_funcao_index({('111', '01/04/2026'): 'ARTIF'})
    base = build_base_cobranca({'ARTIF': 'FÉRIAS'})
    _comparar(*_executar(dados, base, medicao, md, sg))


def test_eq_skip_sg_funcao_nao_classificada():
    dados = [build_dado_ferias_aprovado_1()]
    medicao = build_medicao_index('111', [
        (date(2026, 4, 1), '01/04/2026', [10]),
        (date(2026, 4, 2), '02/04/2026', [11]),
    ])
    md = build_md_cobranca_index({
        ('111', '01/04/2026'): 'CENTRAL',
        ('111', '02/04/2026'): 'CENTRAL',
    })
    sg = build_sg_funcao_index({
        ('111', '01/04/2026'): 'DESCONHECIDO',
        ('111', '02/04/2026'): 'DESCONHECIDO',
    })
    _comparar(*_executar(dados, build_base_cobranca(), medicao, md, sg))


def test_eq_aprovado_2_quando_1_nao_aprovado():
    dados = [build_dado_ferias_aprovado_2(periodo='10/04/2026 a 10/04/2026')]
    medicao = build_medicao_index('111', [(date(2026, 4, 10), '10/04/2026', [42])])
    md = build_md_cobranca_index({('111', '10/04/2026'): 'PACOTE'})
    sg = build_sg_funcao_index({('111', '10/04/2026'): 'X'})
    _comparar(*_executar(dados, build_base_cobranca(), medicao, md, sg))


def test_eq_sem_aprovacao_skip():
    _comparar(*_executar([build_dado_ferias_sem_aprovacao()],
                         build_base_cobranca(), {}, {}, {}))


def test_eq_periodo_invalido():
    _comparar(*_executar([build_dado_ferias_periodo_invalido()],
                         build_base_cobranca(), {}, {}, {}))


def test_eq_periodo_fora_do_mes_skip():
    dados = [build_dado_ferias_aprovado_1(periodo='01/02/2026 a 28/02/2026')]
    _comparar(*_executar(dados, build_base_cobranca(), {}, {}, {}))


def test_eq_intersecao_parcial_clipped():
    dados = [build_dado_ferias_aprovado_1(periodo='28/03/2026 a 02/04/2026')]
    medicao = build_medicao_index('111', [
        (date(2026, 4, 1), '01/04/2026', [10]),
        (date(2026, 4, 2), '02/04/2026', [11]),
    ])
    md = build_md_cobranca_index({
        ('111', '01/04/2026'): 'ADICIONAL',
        ('111', '02/04/2026'): 'ADICIONAL',
    })
    sg = build_sg_funcao_index({
        ('111', '01/04/2026'): 'X', ('111', '02/04/2026'): 'X',
    })
    _comparar(*_executar(dados, build_base_cobranca(), medicao, md, sg))


def test_eq_matricula_nao_encontrada():
    dados = [build_dado_ferias_aprovado_1(chapa='1.999999')]
    _comparar(*_executar(dados, build_base_cobranca(), {}, {}, {}))


def test_eq_rateio_multiplas_linhas():
    dados = [build_dado_ferias_aprovado_1(periodo='01/04/2026 a 01/04/2026')]
    medicao = build_medicao_index('111', [(date(2026, 4, 1), '01/04/2026', [100, 200, 300])])
    md = build_md_cobranca_index({('111', '01/04/2026'): 'ADICIONAL'})
    sg = build_sg_funcao_index({('111', '01/04/2026'): 'X'})
    _comparar(*_executar(dados, build_base_cobranca(), medicao, md, sg))


@pytest.mark.parametrize('chave_omissa', ['situacao', 'md_cobranca', 'sg_funcao'])
def test_eq_col_map_incompleto_levanta_runtime_error(chave_omissa):
    col = build_col_map_sem(chave_omissa)
    with pytest.raises(RuntimeError) as exc_l:
        legacy.gerar_updates_ferias(
            [], build_base_cobranca(), {}, {}, {},
            mes_referencia_padrao(), col,
        )
    with pytest.raises(RuntimeError) as exc_d:
        dominio.gerar_updates_ferias(
            [], build_base_cobranca(), {}, {}, {},
            mes_referencia_padrao(), col,
        )
    assert str(exc_l.value) == str(exc_d.value)


def test_eq_cenario_misto_multiplas_matriculas():
    """Composição: 3 matrículas, classificações distintas, mês completo."""
    dados = [
        build_dado_ferias_aprovado_1(linha=2, chapa='1.000111',
                                     periodo='01/04/2026 a 03/04/2026'),
        build_dado_ferias_aprovado_2(linha=3, chapa='1.000222',
                                     periodo='10/04/2026 a 11/04/2026'),
        build_dado_ferias_aprovado_1(linha=4, chapa='1.000333',
                                     periodo='15/04/2026 a 15/04/2026'),
    ]
    medicao = {
        '111': [(date(2026, 4, d), f'0{d}/04/2026' if d < 10 else f'{d}/04/2026', [10 + d])
                for d in (1, 2, 3)],
        '222': [(date(2026, 4, d), f'{d}/04/2026', [20 + d]) for d in (10, 11)],
        '333': [(date(2026, 4, 15), '15/04/2026', [35])],
    }
    md = {
        ('111', '01/04/2026'): 'ADICIONAL',
        ('111', '02/04/2026'): 'ADICIONAL',
        ('111', '03/04/2026'): 'ADICIONAL',
        ('222', '10/04/2026'): 'CENTRAL',
        ('222', '11/04/2026'): 'CENTRAL',
        ('333', '15/04/2026'): 'CENTRAL',
    }
    sg = {
        ('111', '01/04/2026'): 'X',
        ('111', '02/04/2026'): 'X',
        ('111', '03/04/2026'): 'X',
        ('222', '10/04/2026'): 'AJUD-CIVIL',
        ('222', '11/04/2026'): 'AJUD-CIVIL',
        ('333', '15/04/2026'): 'DESCONHECIDO',
    }
    base = build_base_cobranca({'AJUD-CIVIL': 'FÉRIAS S/ DESC', 'X': 'FÉRIAS'})
    _comparar(*_executar(dados, base, medicao, md, sg))
