"""mes_referencia_unico — invariante de mês único, streaming + early-exit."""

from __future__ import annotations

import pytest

from app.domain.errors import PlanilhaInvalidaError
from app.domain.reference_month import mes_referencia_unico


def test_retorna_par_quando_consistente():
    assert mes_referencia_unico(
        [(2026, 3), (2026, 3), None, (2026, 3)],
        contexto="X",
    ) == (2026, 3)


def test_aceita_generator():
    def gen():
        yield (2026, 5)
        yield None
        yield (2026, 5)

    assert mes_referencia_unico(gen(), contexto="X") == (2026, 5)


def test_levanta_em_multimes_com_ambos_meses_na_mensagem():
    with pytest.raises(PlanilhaInvalidaError) as exc:
        mes_referencia_unico(
            [(2026, 3), (2026, 4)],
            contexto="Medição",
        )
    msg = str(exc.value)
    assert "2026-03" in msg
    assert "2026-04" in msg
    assert "Medição" in msg


def test_early_exit_nao_consome_resto_em_mismatch():
    consumed: list[tuple[int, int] | None] = []

    def gen():
        for p in [(2026, 1), (2026, 2), (2026, 3), (2026, 4)]:
            consumed.append(p)
            yield p

    with pytest.raises(PlanilhaInvalidaError):
        mes_referencia_unico(gen(), contexto="X")
    assert consumed == [(2026, 1), (2026, 2)]


def test_levanta_quando_vazio():
    with pytest.raises(PlanilhaInvalidaError, match="sem datas"):
        mes_referencia_unico([], contexto="Catálogo")


def test_levanta_quando_so_none():
    with pytest.raises(PlanilhaInvalidaError, match="sem datas"):
        mes_referencia_unico([None, None, None], contexto="X")
