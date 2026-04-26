from datetime import date

import pytest

from app.domain.errors import PlanilhaInvalidaError
from app.pipeline import _mes_referencia


def test_mes_referencia_unico_mes_retorna_dia_1():
    medicao = {
        '111': [(date(2026, 3, 18), '18/03/2026', [2])],
        '222': [(date(2026, 3, 31), '31/03/2026', [3])],
    }
    assert _mes_referencia(medicao) == date(2026, 3, 1)


def test_mes_referencia_multi_mes_levanta():
    medicao = {
        '111': [(date(2026, 3, 31), '31/03/2026', [2])],
        '222': [(date(2026, 4, 1), '01/04/2026', [3])],
    }
    with pytest.raises(PlanilhaInvalidaError) as exc:
        _mes_referencia(medicao)
    msg = str(exc.value)
    assert '2026-03' in msg
    assert '2026-04' in msg


def test_mes_referencia_vazio_levanta_runtime():
    with pytest.raises(RuntimeError):
        _mes_referencia({})
