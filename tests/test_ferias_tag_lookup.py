"""gerar_updates_ferias com base_tags: match, miss, dedup, e backward compat."""

from __future__ import annotations

from datetime import date

from app.domain import ferias
from app.domain.ferias import FeriasContext
from tests.fixtures.ferias_factories import (
    build_base_cobranca,
    build_col_map,
    build_dado_ferias_aprovado_1,
    build_md_cobranca_index,
    build_sg_funcao_index,
    mes_referencia_padrao,
)


def _setup(base_tags=None, unidade_por_chave=None):
    dados = [
        build_dado_ferias_aprovado_1(linha=2, chapa='1.000111',
                                     periodo='01/04/2026 a 02/04/2026'),
    ]
    medicao = {
        '111': [
            (date(2026, 4, 1), '01/04/2026', [10]),
            (date(2026, 4, 2), '02/04/2026', [11]),
        ],
    }
    md = build_md_cobranca_index({
        ('111', '01/04/2026'): 'PACOTE',
        ('111', '02/04/2026'): 'PACOTE',
    })
    sg = build_sg_funcao_index({
        ('111', '01/04/2026'): 'MECANICO',
        ('111', '02/04/2026'): 'MECANICO',
    })
    return FeriasContext(
        base_cobranca=build_base_cobranca(),
        medicao_por_matricula=medicao,
        md_cobranca_por_chave=md,
        sg_funcao_por_chave=sg,
        unidade_por_chave=unidade_por_chave or {
            ('111', '01/04/2026'): 'UN-A',
            ('111', '02/04/2026'): 'UN-A',
        },
        base_tags_por_chave=base_tags or {},
        mes_referencia=mes_referencia_padrao(),
        col_map=build_col_map(),
    ), dados


def test_lookup_hit_seta_update_tag():
    ctx, dados = _setup(base_tags={
        ('MECANICO', 'UN-A', 'PACOTE', 'FERIAS'): 'M-A-PA-FE',
    })
    atus, incs = ferias.gerar_updates_ferias(dados, ctx)
    assert len(atus) == 2
    assert all(u.tag == 'M-A-PA-FE' for u in atus)
    assert incs == []


def test_lookup_miss_dedupedados_em_uma_inconsistencia():
    """Mesma chave normalizada para 2 rows (mesma matrícula, datas distintas)
    + 1 segunda matrícula com mesma chave → 1 inconsistência total com 2 mats."""
    ctx, dados = _setup(base_tags={
        ('OUTRO', 'UN-A', 'PACOTE', 'FERIAS'): 'IRRELEVANTE',
    })
    # adiciona segunda matrícula compartilhando a mesma chave
    ctx2 = FeriasContext(
        base_cobranca=ctx.base_cobranca,
        medicao_por_matricula={
            **ctx.medicao_por_matricula,
            '222': [(date(2026, 4, 1), '01/04/2026', [20])],
        },
        md_cobranca_por_chave={**ctx.md_cobranca_por_chave,
                               ('222', '01/04/2026'): 'PACOTE'},
        sg_funcao_por_chave={**ctx.sg_funcao_por_chave,
                             ('222', '01/04/2026'): 'MECANICO'},
        unidade_por_chave={**ctx.unidade_por_chave,
                           ('222', '01/04/2026'): 'UN-A'},
        base_tags_por_chave=ctx.base_tags_por_chave,
        mes_referencia=ctx.mes_referencia,
        col_map=ctx.col_map,
    )
    dados2 = dados + [
        build_dado_ferias_aprovado_1(linha=3, chapa='1.000222',
                                     periodo='01/04/2026 a 01/04/2026'),
    ]
    atus, incs = ferias.gerar_updates_ferias(dados2, ctx2)
    assert atus == []
    assert len(incs) == 1
    assert incs[0].origem == 'ferias'
    erro = incs[0].erro
    assert 'tag não mapeada' in erro
    assert 'MECANICO' in erro
    assert '111' in erro and '222' in erro
    assert '2 matrícula' in erro


def test_base_tags_vazia_nao_emite_inconsistencia_nem_seta_tag():
    """Migração aditiva: sem base_tags, comportamento legacy preservado."""
    ctx, dados = _setup(base_tags={})
    atus, incs = ferias.gerar_updates_ferias(dados, ctx)
    assert len(atus) == 2
    assert all(u.tag is None for u in atus)
    assert incs == []


def test_chaves_diferentes_geram_inconsistencias_distintas():
    ctx, dados = _setup(base_tags={
        ('OUTRO', 'UN-X', 'X', 'X'): 'X',
    })
    # adicionar matrícula com chave distinta (situacao FERIAS S/ DESC)
    ctx2 = FeriasContext(
        base_cobranca={'AJUD': 'FÉRIAS S/ DESC'},
        medicao_por_matricula={
            **ctx.medicao_por_matricula,
            '222': [(date(2026, 4, 5), '05/04/2026', [25])],
        },
        md_cobranca_por_chave={**ctx.md_cobranca_por_chave,
                               ('222', '05/04/2026'): 'CENTRAL'},
        sg_funcao_por_chave={**ctx.sg_funcao_por_chave,
                             ('222', '05/04/2026'): 'AJUD'},
        unidade_por_chave={**ctx.unidade_por_chave,
                           ('222', '05/04/2026'): 'UN-B'},
        base_tags_por_chave=ctx.base_tags_por_chave,
        mes_referencia=ctx.mes_referencia,
        col_map=ctx.col_map,
    )
    dados2 = dados + [
        build_dado_ferias_aprovado_1(linha=3, chapa='1.000222',
                                     periodo='05/04/2026 a 05/04/2026'),
    ]
    atus, incs = ferias.gerar_updates_ferias(dados2, ctx2)
    assert atus == []
    assert len(incs) == 2  # uma por chave normalizada distinta


def test_assinatura_legacy_posicional_compativel():
    """Pipeline antigo (assinatura posicional) ainda funciona."""
    dados = [
        build_dado_ferias_aprovado_1(linha=2, chapa='1.000111',
                                     periodo='01/04/2026 a 01/04/2026'),
    ]
    medicao = {
        '111': [(date(2026, 4, 1), '01/04/2026', [10])],
    }
    atus, _ = ferias.gerar_updates_ferias(
        dados,
        build_base_cobranca(),
        medicao,
        build_md_cobranca_index({('111', '01/04/2026'): 'PACOTE'}),
        build_sg_funcao_index({('111', '01/04/2026'): 'X'}),
        mes_referencia_padrao(),
        build_col_map(),
    )
    assert len(atus) == 1
    assert atus[0].tag is None
