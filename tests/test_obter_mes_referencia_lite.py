"""Testes de obter_mes_referencia_medicao_lite — primeira data vence."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.errors import PlanilhaInvalidaError
from app.infrastructure.data.bootstrap import obter_mes_referencia_medicao_lite

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
MEDICAO_MOCK = FIXTURES / 'medicao_mock.xlsx'


def test_primeira_data_valida_vence():
    mes = obter_mes_referencia_medicao_lite(str(MEDICAO_MOCK))
    assert isinstance(mes, str)
    assert len(mes) == 7
    assert mes[4] == '-'
    ano, mm = mes.split('-')
    assert ano.isdigit() and mm.isdigit()


def test_arquivo_inexistente_propaga_erro_de_leitura(tmp_path):
    p = tmp_path / 'no.xlsx'
    with pytest.raises((FileNotFoundError, OSError, ValueError, PlanilhaInvalidaError)):
        obter_mes_referencia_medicao_lite(str(p))
