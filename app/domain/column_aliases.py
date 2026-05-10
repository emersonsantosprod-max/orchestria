"""
column_aliases.py — aliases canônicos de colunas da Medição.

Cada alias é a forma normalizada do header (lowercase + accent-fold +
whitespace-collapse) — `mapear_colunas` produz a forma normalizada via
`_normalizar_header` antes de comparar. Determinismo: primeiro alias
da lista vence em case de match exato; ambiguidade entre chaves
distintas é detectada pelo caller.

Adições 4b: `unidade` (lookup de base_tags).
"""

from __future__ import annotations

COLUMN_ALIASES: dict[str, list[str]] = {
    'data':         ['data'],
    'matricula':    ['re', 'matricula'],
    'desconto':     ['descontos'],
    'observacao':   ['observacao', 'observacoes'],
    'situacao':     ['situacao'],
    'md_cobranca':  ['md cobranca'],
    'sg_funcao':    ['sg funcao'],
    'unidade':      ['unidade', 'und', 'unid'],
    'tag':          ['tag'],
    'pct_cobranca': ['% cobranca', 'pct cobranca'],
}

OBRIGATORIAS = ('data', 'matricula', 'desconto', 'observacao')
