"""Contract guard de app.domain.distribuicao + app.application.services.validacao_distribuicao.

Pinniza invariantes estruturais permanentes — distinto da cobertura
per-rule em test_validar_distribuicao.py.

Cobre:
  - Tipos de retorno (list[InconsistenciaDistribuicao],
    list[core.Inconsistencia], str).
  - validar_para_dominio: origem='writer', linha='-', matricula==funcao,
    formato exato da string de erro.
  - validar_aderencia_distribuicao: ordenacao deterministica
    (data, funcao, md_cobranca).
  - gerar_relatorio: 4 secoes obrigatorias, retorno str.
  - Idempotencia: chamadas repetidas com mesma entrada -> mesma saida.
"""

from __future__ import annotations

import re

from app.application.services.validacao_distribuicao import validar_para_dominio
from app.domain.core import Inconsistencia
from app.domain.distribuicao import (
    InconsistenciaDistribuicao,
    gerar_relatorio,
    validar_aderencia_distribuicao,
)
from tests.fixtures.distribuicao_factories import (
    build_bd_record,
    build_medicao_record,
    build_registros,
)

ERRO_FMT_RE = re.compile(
    r'^(ERRO_LINHA_AUSENTE|ERRO_INSUFICIENCIA_RATEIO|ERRO_EXCESSO_RATEIO) '
    r'\[[^\]]+\] esperado=-?\d+\.\d{4} realizado=-?\d+\.\d{4} diff=-?\d+\.\d{4}$'
)


def _entrada_mista():
    bd = [
        build_bd_record(funcao='Z', md_cobranca='CENTRAL', quantidade=1.0),
        build_bd_record(funcao='A', md_cobranca='HD',      quantidade=0.5),
        build_bd_record(funcao='A', md_cobranca='ADM-B',   quantidade=0.7),
    ]
    medicao = [
        build_medicao_record(data='02/04/2026', sg_funcao='A', md_cobranca='HD',      pct_cobranca=0.5),
        build_medicao_record(data='01/04/2026', sg_funcao='Z', md_cobranca='CENTRAL', pct_cobranca=0.4),
        build_medicao_record(data='02/04/2026', sg_funcao='A', md_cobranca='ADM-B',   pct_cobranca=0.3),
    ]
    return bd, medicao


def test_validar_aderencia_retorna_lista_de_dataclass():
    bd, medicao = _entrada_mista()
    out = validar_aderencia_distribuicao(bd, medicao)
    assert isinstance(out, list)
    assert all(isinstance(x, InconsistenciaDistribuicao) for x in out)


def test_validar_aderencia_ordenacao_deterministica():
    bd, medicao = _entrada_mista()
    out = validar_aderencia_distribuicao(bd, medicao)
    chaves = [(x.data, x.funcao, x.md_cobranca) for x in out]
    assert chaves == sorted(chaves)


def test_validar_para_dominio_retorna_lista_de_inconsistencia():
    bd, medicao = _entrada_mista()
    out = validar_para_dominio(bd, medicao)
    assert isinstance(out, list)
    assert all(isinstance(x, Inconsistencia) for x in out)


def test_validar_para_dominio_origem_e_linha_constantes():
    bd, medicao = _entrada_mista()
    out = validar_para_dominio(bd, medicao)
    assert out, 'cenario deve emitir pelo menos uma inconsistencia'
    for inc in out:
        assert inc.origem == 'writer'
        assert inc.linha == '-'


def test_validar_para_dominio_matricula_eh_funcao():
    bd, medicao = _entrada_mista()
    raw = validar_aderencia_distribuicao(bd, medicao)
    out = validar_para_dominio(bd, medicao)
    assert [i.matricula for i in out] == [r.funcao for r in raw]


def test_validar_para_dominio_formato_exato_da_mensagem():
    bd, medicao = _entrada_mista()
    out = validar_para_dominio(bd, medicao)
    for inc in out:
        assert ERRO_FMT_RE.match(inc.erro), inc.erro


def test_gerar_relatorio_retorna_str_com_4_secoes():
    bd, medicao = _entrada_mista()
    incs = validar_aderencia_distribuicao(bd, medicao)
    txt = gerar_relatorio(incs, build_registros(), n_pares_bd=3, n_datas=2, avisos_import=[])
    assert isinstance(txt, str)
    for secao in ('ETAPA 1 — DOCUMENTAÇÃO', 'ETAPA 2 — RESUMO',
                  'ETAPA 3 — DETALHES', 'ETAPA 4 — CONCLUSÃO'):
        assert secao in txt


def test_idempotencia_validar_aderencia():
    bd, medicao = _entrada_mista()
    a = validar_aderencia_distribuicao(bd, medicao)
    b = validar_aderencia_distribuicao(bd, medicao)
    assert a == b


def test_idempotencia_validar_para_dominio():
    bd, medicao = _entrada_mista()
    assert validar_para_dominio(bd, medicao) == validar_para_dominio(bd, medicao)


def test_entrada_vazia_retorna_listas_vazias():
    assert validar_aderencia_distribuicao([], []) == []
    assert validar_para_dominio([], []) == []
