"""Caracterização do legacy app.validar_distribuicao.

Suite descartável — deletada no Step 5 quando o legacy for removido.
"""

from __future__ import annotations

from app.validar_distribuicao import (
    ERRO_EXCESSO_RATEIO,
    ERRO_INSUFICIENCIA_RATEIO,
    ERRO_LINHA_AUSENTE,
    gerar_relatorio,
    validar_aderencia_distribuicao,
    validar_para_dominio,
)
from tests.fixtures.distribuicao_factories import (
    build_bd_record,
    build_medicao_record,
    build_registros,
)


def test_validar_aderencia_emite_linha_ausente_quando_realizado_zero():
    bd = [build_bd_record(funcao='OP', md_cobranca='CENTRAL', quantidade=1.0)]
    medicao = [build_medicao_record(data='01/04/2026', sg_funcao='OP',
                                    md_cobranca='ADM-B', pct_cobranca=1.0)]
    incs = validar_aderencia_distribuicao(bd, medicao)
    assert len(incs) == 1
    assert incs[0].tipo_inconsistencia == ERRO_LINHA_AUSENTE
    assert incs[0].md_cobranca == 'CENTRAL'
    assert incs[0].realizado == 0.0


def test_validar_aderencia_emite_insuficiencia_quando_diff_negativo():
    bd = [build_bd_record(quantidade=1.0)]
    medicao = [build_medicao_record(pct_cobranca=0.4)]
    incs = validar_aderencia_distribuicao(bd, medicao)
    assert len(incs) == 1
    assert incs[0].tipo_inconsistencia == ERRO_INSUFICIENCIA_RATEIO
    assert incs[0].diff < 0


def test_validar_aderencia_emite_excesso_quando_diff_positivo():
    bd = [build_bd_record(quantidade=1.0)]
    medicao = [build_medicao_record(pct_cobranca=1.5)]
    incs = validar_aderencia_distribuicao(bd, medicao)
    assert len(incs) == 1
    assert incs[0].tipo_inconsistencia == ERRO_EXCESSO_RATEIO
    assert incs[0].diff > 0


def test_validar_aderencia_ordenacao_estavel():
    bd = [
        build_bd_record(funcao='B', md_cobranca='CENTRAL', quantidade=1.0),
        build_bd_record(funcao='A', md_cobranca='HD',      quantidade=1.0),
        build_bd_record(funcao='A', md_cobranca='ADM-B',   quantidade=1.0),
    ]
    medicao = [
        build_medicao_record(data='02/04/2026', sg_funcao='A', md_cobranca='HD',    pct_cobranca=0.5),
        build_medicao_record(data='01/04/2026', sg_funcao='B', md_cobranca='CENTRAL', pct_cobranca=0.5),
        build_medicao_record(data='02/04/2026', sg_funcao='A', md_cobranca='ADM-B',   pct_cobranca=0.5),
    ]
    incs = validar_aderencia_distribuicao(bd, medicao)
    chaves = [(i.data, i.funcao, i.md_cobranca) for i in incs]
    assert chaves == sorted(chaves)


def test_validar_aderencia_multi_data_independente():
    bd = [build_bd_record(quantidade=1.0)]
    medicao = [
        build_medicao_record(data='01/04/2026', pct_cobranca=1.0),
        build_medicao_record(data='02/04/2026', pct_cobranca=0.5),
    ]
    incs = validar_aderencia_distribuicao(bd, medicao)
    assert len(incs) == 1
    assert incs[0].data == '02/04/2026'
    assert incs[0].tipo_inconsistencia == ERRO_INSUFICIENCIA_RATEIO


def test_validar_para_dominio_formato_e_origem():
    bd = [build_bd_record(funcao='OP', md_cobranca='CENTRAL', quantidade=1.0)]
    medicao = [build_medicao_record(sg_funcao='OP', md_cobranca='CENTRAL', pct_cobranca=0.4)]
    out = validar_para_dominio(bd, medicao)
    assert len(out) == 1
    inc = out[0]
    assert inc.origem == 'writer'
    assert inc.linha == '-'
    assert inc.matricula == 'OP'
    assert inc.data == '01/04/2026'
    assert inc.erro == (
        f'{ERRO_INSUFICIENCIA_RATEIO} [CENTRAL] '
        f'esperado=1.0000 realizado=0.4000 diff=-0.6000'
    )


def test_gerar_relatorio_4_secoes_e_resumo():
    bd = [build_bd_record(quantidade=1.0)]
    medicao = [build_medicao_record(pct_cobranca=0.4)]
    incs = validar_aderencia_distribuicao(bd, medicao)
    txt = gerar_relatorio(incs, build_registros(), n_pares_bd=1, n_datas=1, avisos_import=[])
    assert 'ETAPA 1 — DOCUMENTAÇÃO' in txt
    assert 'ETAPA 2 — RESUMO' in txt
    assert 'ETAPA 3 — DETALHES' in txt
    assert 'ETAPA 4 — CONCLUSÃO' in txt
    assert ERRO_INSUFICIENCIA_RATEIO in txt
    assert 'VALIDAÇÃO CONCLUÍDA: INCONSISTÊNCIAS ENCONTRADAS' in txt


def test_gerar_relatorio_aprovada_quando_sem_inconsistencia():
    txt = gerar_relatorio([], build_registros(), n_pares_bd=0, n_datas=0, avisos_import=[])
    assert 'VALIDAÇÃO CONCLUÍDA: APROVADA' in txt
    assert 'Nenhuma inconsistência encontrada.' in txt
