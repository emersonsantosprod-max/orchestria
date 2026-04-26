"""Builders pequenos para entradas de validar_aderencia_distribuicao
e validar_para_dominio.

Cada factory retorna a estrutura mínima esperada; suites compõem
cenários inline e mantêm as próprias asserções.
"""

from __future__ import annotations


def build_bd_record(funcao='OPERADOR', md_cobranca='CENTRAL',
                    area=None, quantidade=1.0):
    return {
        'funcao': funcao,
        'md_cobranca': md_cobranca,
        'area': area,
        'quantidade': quantidade,
    }


def build_medicao_record(data='01/04/2026', sg_funcao='OPERADOR',
                         md_cobranca='CENTRAL', pct_cobranca=1.0):
    return {
        'data': data,
        'sg_funcao': sg_funcao,
        'md_cobranca': md_cobranca,
        'pct_cobranca': pct_cobranca,
    }


def build_registros(bd_caminho='bd.xlsx', bd_em='2026-04-01T00:00:00',
                    med_caminho='medicao.xlsx', med_em='2026-04-01T00:00:00'):
    return {
        'bd':      {'caminho': bd_caminho,  'importado_em': bd_em},
        'medicao': {'caminho': med_caminho, 'importado_em': med_em},
    }
