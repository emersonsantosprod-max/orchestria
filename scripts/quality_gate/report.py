"""Formatação da tabela e avaliação de regressão."""

from __future__ import annotations

ABSOLUTOS = ('violations', 'oversized_files')
ORDEM = ('violations', 'oversized_files', 'lines', 'functions', 'statements')

TOLERANCIA_PCT_DEFAULT = {'lines': 5.0, 'functions': 5.0, 'statements': 5.0}


def _delta_str(item: str, base: int, cur: int) -> str:
    diff = cur - base
    if item in ABSOLUTOS:
        sinal = '+' if diff > 0 else ''
        return f'{sinal}{diff}'
    if base == 0:
        return '+∞%' if diff > 0 else '0%'
    pct = (diff / base) * 100
    sinal = '+' if pct > 0 else ''
    return f'{sinal}{pct:.2f}%'


def formatar_tabela(baseline: dict, current: dict) -> str:
    linhas = [
        '| item            | baseline | current |     delta |',
        '|-----------------|---------:|--------:|----------:|',
    ]
    for item in ORDEM:
        b = baseline.get(item, 0)
        c = current.get(item, 0)
        linhas.append(f'| {item:<15} | {b:>8} | {c:>7} | {_delta_str(item, b, c):>9} |')
    return '\n'.join(linhas)


def avaliar_regressao(
    baseline: dict,
    current: dict,
    tolerancia_pct: dict[str, float] | None = None,
) -> bool:
    tol = tolerancia_pct or TOLERANCIA_PCT_DEFAULT
    for item in ABSOLUTOS:
        if current.get(item, 0) > baseline.get(item, 0):
            return True
    for item, limite in tol.items():
        b = baseline.get(item, 0)
        c = current.get(item, 0)
        if b == 0:
            if c > 0:
                return True
            continue
        if (c - b) / b * 100 > limite:
            return True
    return False
