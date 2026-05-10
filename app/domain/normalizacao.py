"""
normalizacao.py — chave canônica domain-wide.

`normalizar` aplica NFKD + remoção de combining marks + colapso de
whitespace + UPPER. Casefold-equivalente para os caracteres latinos
do domínio (após accent-fold + UPPER, comparações ficam estáveis).

`normalizar_chave(*parts)` é o entry point para qualquer chave de
lookup (base_cobranca, base_tags, lookups futuros).
"""

from __future__ import annotations

import unicodedata


def normalizar(value) -> str:
    if value is None:
        return ''
    s = unicodedata.normalize('NFKD', str(value))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = ' '.join(s.split())
    return s.upper()


def normalizar_chave(*parts) -> tuple[str, ...]:
    return tuple(normalizar(p) for p in parts)
