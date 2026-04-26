"""Caracterização comportamental de app.ferias (legacy).

Oracle congelado das ramificações de gerar_updates_ferias usado pelo
Step 3 (equivalência legacy ≡ domain). Disposável: deletado no Step 5.

Cada teste compõe seus inputs inline via tests.fixtures.ferias_factories
e mantém suas próprias asserções — sem listas frozen compartilhadas.
"""

from __future__ import annotations

from datetime import date

import pytest

from app import ferias as legacy
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


def _norm_updates(updates):
    return sorted(
        [
            (u.tipo, u.matricula, u.data, u.observacao, u.situacao,
             u.sobrescrever_obs, u.row, u.desconto_min)
            for u in updates
        ],
        key=lambda t: (t[1], t[2], t[6] if t[6] is not None else -1),
    )


def _norm_incs(incs):
    return sorted(
        [(i.origem, i.matricula, i.data, i.erro, i.linha) for i in incs],
        key=lambda t: (t[0], t[1] or '', t[2] or '', t[3] or '', str(t[4])),
    )


def test_lista_vazia():
    atus, incs = legacy.gerar_updates_ferias(
        [], build_base_cobranca(), {}, {}, {},
        mes_referencia_padrao(), build_col_map(),
    )
    assert atus == []
    assert incs == []


def test_aprovado_1_ferias_direto():
    dados = [build_dado_ferias_aprovado_1()]
    medicao = build_medicao_index('111', [(date(2026, 4, 1), '01/04/2026', [10])])
    md = build_md_cobranca_index({('111', '01/04/2026'): 'ADICIONAL'})
    sg = build_sg_funcao_index({('111', '01/04/2026'): 'X'})

    atus, incs = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), medicao, md, sg,
        mes_referencia_padrao(), build_col_map(),
    )

    assert incs == []
    assert _norm_updates(atus) == [
        ('ferias', '111', '01/04/2026', '01/04 a 03/04 - FÉRIAS',
         'FÉRIAS', True, 10, None),
    ]


def test_aprovado_2_quando_1_nao_aprovado():
    dados = [build_dado_ferias_aprovado_2(periodo='10/04/2026 a 10/04/2026')]
    medicao = build_medicao_index('111', [(date(2026, 4, 10), '10/04/2026', [42])])
    md = build_md_cobranca_index({('111', '10/04/2026'): 'PACOTE'})
    sg = build_sg_funcao_index({('111', '10/04/2026'): 'X'})

    atus, _ = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), medicao, md, sg,
        mes_referencia_padrao(), build_col_map(),
    )
    assert len(atus) == 1
    assert atus[0].observacao == '10/04 a 10/04 - FÉRIAS'


def test_sem_aprovacao_skip_silencioso():
    dados = [build_dado_ferias_sem_aprovacao()]
    atus, incs = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), {}, {}, {},
        mes_referencia_padrao(), build_col_map(),
    )
    assert atus == []
    assert incs == []


def test_periodo_invalido_emite_inconsistencia():
    dados = [build_dado_ferias_periodo_invalido()]
    atus, incs = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), {}, {}, {},
        mes_referencia_padrao(), build_col_map(),
    )
    assert atus == []
    assert _norm_incs(incs) == [
        ('ferias', '1.000111', 'xx/yy/zzzz', 'período inválido', 2),
    ]


def test_periodo_fora_do_mes_skip_silencioso():
    dados = [build_dado_ferias_aprovado_1(periodo='01/02/2026 a 28/02/2026')]
    atus, incs = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), {}, {}, {},
        mes_referencia_padrao(), build_col_map(),
    )
    assert atus == []
    assert incs == []


def test_intersecao_parcial_clipped_para_mes():
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

    atus, _ = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), medicao, md, sg,
        mes_referencia_padrao(), build_col_map(),
    )
    assert {a.data for a in atus} == {'01/04/2026', '02/04/2026'}
    assert all(a.observacao == '28/03 a 02/04 - FÉRIAS' for a in atus)


def test_ferias_sd_emite_sufixo_nao_desconta():
    dados = [build_dado_ferias_aprovado_1()]
    medicao = build_medicao_index('111', [(date(2026, 4, 1), '01/04/2026', [10])])
    md = build_md_cobranca_index({('111', '01/04/2026'): 'CENTRAL'})
    sg = build_sg_funcao_index({('111', '01/04/2026'): 'AJUD-CIVIL'})
    base = build_base_cobranca({'AJUD-CIVIL': 'FÉRIAS S/ DESC'})

    atus, _ = legacy.gerar_updates_ferias(
        dados, base, medicao, md, sg,
        mes_referencia_padrao(), build_col_map(),
    )
    assert atus[0].situacao == 'FÉRIAS S/ DESC'
    assert atus[0].observacao == '01/04 a 03/04 - FÉRIAS (NÃO DESCONTA)'


def test_lookup_sg_funcao_categoria_outra_emite_sem_sufixo():
    dados = [build_dado_ferias_aprovado_1()]
    medicao = build_medicao_index('111', [(date(2026, 4, 1), '01/04/2026', [10])])
    md = build_md_cobranca_index({('111', '01/04/2026'): 'CENTRAL'})
    sg = build_sg_funcao_index({('111', '01/04/2026'): 'ARTIF'})
    base = build_base_cobranca({'ARTIF': 'FÉRIAS'})

    atus, _ = legacy.gerar_updates_ferias(
        dados, base, medicao, md, sg,
        mes_referencia_padrao(), build_col_map(),
    )
    assert atus[0].situacao == 'FÉRIAS'
    assert atus[0].observacao == '01/04 a 03/04 - FÉRIAS'


def test_sg_funcao_nao_classificada_dedup_por_matricula_sg():
    dados = [build_dado_ferias_aprovado_1()]
    medicao = build_medicao_index('111', [
        (date(2026, 4, 1), '01/04/2026', [10]),
        (date(2026, 4, 2), '02/04/2026', [11]),
        (date(2026, 4, 3), '03/04/2026', [12]),
    ])
    md = build_md_cobranca_index({
        ('111', '01/04/2026'): 'CENTRAL',
        ('111', '02/04/2026'): 'CENTRAL',
        ('111', '03/04/2026'): 'CENTRAL',
    })
    sg = build_sg_funcao_index({
        ('111', '01/04/2026'): 'DESCONHECIDO',
        ('111', '02/04/2026'): 'DESCONHECIDO',
        ('111', '03/04/2026'): 'DESCONHECIDO',
    })

    atus, incs = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), medicao, md, sg,
        mes_referencia_padrao(), build_col_map(),
    )
    assert atus == []
    assert len(incs) == 1
    assert incs[0].erro == 'sg função não classificada'


def test_matricula_nao_encontrada():
    dados = [build_dado_ferias_aprovado_1(chapa='1.999999')]
    atus, incs = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), {}, {}, {},
        mes_referencia_padrao(), build_col_map(),
    )
    assert atus == []
    assert _norm_incs(incs) == [
        ('ferias', '999999', '01/04/2026 a 03/04/2026',
         'matrícula não encontrada', 2),
    ]


def test_col_map_sem_situacao_levanta_runtime_error():
    with pytest.raises(RuntimeError, match='situacao'):
        legacy.gerar_updates_ferias(
            [], build_base_cobranca(), {}, {}, {},
            mes_referencia_padrao(), build_col_map_sem('situacao'),
        )


def test_col_map_sem_md_cobranca_levanta_runtime_error():
    with pytest.raises(RuntimeError, match='md_cobranca'):
        legacy.gerar_updates_ferias(
            [], build_base_cobranca(), {}, {}, {},
            mes_referencia_padrao(), build_col_map_sem('md_cobranca'),
        )


def test_col_map_sem_sg_funcao_levanta_runtime_error():
    with pytest.raises(RuntimeError, match='sg_funcao'):
        legacy.gerar_updates_ferias(
            [], build_base_cobranca(), {}, {}, {},
            mes_referencia_padrao(), build_col_map_sem('sg_funcao'),
        )


def test_rateio_uma_data_multiplas_linhas():
    dados = [build_dado_ferias_aprovado_1(periodo='01/04/2026 a 01/04/2026')]
    medicao = build_medicao_index('111', [(date(2026, 4, 1), '01/04/2026', [100, 200, 300])])
    md = build_md_cobranca_index({('111', '01/04/2026'): 'ADICIONAL'})
    sg = build_sg_funcao_index({('111', '01/04/2026'): 'X'})

    atus, _ = legacy.gerar_updates_ferias(
        dados, build_base_cobranca(), medicao, md, sg,
        mes_referencia_padrao(), build_col_map(),
    )
    assert sorted(a.row for a in atus) == [100, 200, 300]
