"""reference_month — invariante de mês único em coleções de datas.

Domain-only: não importa sqlite/openpyxl/filesystem. Recebe pares
(ano, mês) já normalizados pela infraestrutura — datetime/date/strings
ficam fora desta camada.

Invariante: todas as datas não-nulas de uma planilha (medição, base de
treinamentos, etc.) devem pertencer ao mesmo mês civil. Se houver mais
de um mês, a planilha é inválida.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.domain.errors import PlanilhaInvalidaError


def mes_referencia_unico(
    pares: Iterable[tuple[int, int] | None],
    *,
    contexto: str,
) -> tuple[int, int]:
    """Retorna o (ano, mês) único entre os pares não-nulos.

    Streaming + early-exit: para na primeira divergência. Aceita
    generators — não materializa coleção intermediária.

    Levanta PlanilhaInvalidaError se:
      - nenhum par válido for encontrado;
      - dois pares distintos forem encontrados.
    """
    primeiro: tuple[int, int] | None = None
    for p in pares:
        if p is None:
            continue
        if primeiro is None:
            primeiro = p
            continue
        if p != primeiro:
            a, b = sorted([primeiro, p])
            raise PlanilhaInvalidaError(
                f"{contexto} com múltiplos meses: "
                f"{a[0]:04d}-{a[1]:02d}, {b[0]:04d}-{b[1]:02d}"
            )
    if primeiro is None:
        raise PlanilhaInvalidaError(f"{contexto} sem datas válidas")
    return primeiro
