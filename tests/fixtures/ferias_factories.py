"""Builders pequenos e composáveis para entradas de gerar_updates_ferias.

Cada factory retorna a estrutura mínima esperada por
gerar_updates_ferias; suites de teste compõem cenários inline e mantêm
as próprias asserções, evitando single-source-of-truth.
"""

from __future__ import annotations

from datetime import date


def build_dado_ferias_aprovado_1(linha=2, chapa='1.000111',
                                 periodo='01/04/2026 a 03/04/2026'):
    return {
        'linha': linha, 'chapa': chapa,
        'p1': periodo, 's1': 'Aprovado',
        'p2': None, 's2': None,
    }


def build_dado_ferias_aprovado_2(linha=2, chapa='1.000111',
                                 periodo='10/04/2026 a 12/04/2026'):
    return {
        'linha': linha, 'chapa': chapa,
        'p1': '01/01/2026 a 02/01/2026', 's1': 'Pendente',
        'p2': periodo, 's2': 'Aprovado',
    }


def build_dado_ferias_sem_aprovacao(linha=2, chapa='1.000111'):
    return {
        'linha': linha, 'chapa': chapa,
        'p1': '01/04/2026 a 03/04/2026', 's1': 'Pendente',
        'p2': None, 's2': None,
    }


def build_dado_ferias_periodo_invalido(linha=2, chapa='1.000111',
                                       periodo='xx/yy/zzzz'):
    return {
        'linha': linha, 'chapa': chapa,
        'p1': periodo, 's1': 'Aprovado',
        'p2': None, 's2': None,
    }


def build_medicao_index(matricula, datas):
    """datas: list[(date_obj, data_str, list[row_idx])]."""
    return {matricula: list(datas)}


def build_md_cobranca_index(entries):
    """entries: dict[(matricula, data_str), str]."""
    return dict(entries)


def build_sg_funcao_index(entries):
    """entries: dict[(matricula, data_str), str]."""
    return dict(entries)


def build_base_cobranca(entries=None):
    """entries: dict[sg_funcao_upper, categoria]."""
    return dict(entries or {})


def build_col_map(extras=None):
    base = {
        'data': 0, 'matricula': 1, 'desconto': 2, 'observacao': 3,
        'situacao': 4, 'md_cobranca': 5, 'sg_funcao': 6, '_header_row': 1,
    }
    if extras:
        base.update(extras)
    return base


def build_col_map_sem(*chaves):
    """col_map sem as chaves indicadas — útil para forçar RuntimeError."""
    cm = build_col_map()
    for k in chaves:
        cm.pop(k, None)
    return cm


def mes_referencia_padrao():
    return date(2026, 4, 1)
