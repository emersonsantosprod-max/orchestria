"""SSOT pin: derivar_mes_referencia_da_medicao must equal _mes_referencia.

Boundary used by /api/session/medicao (and any non-pipeline entry-point that
needs mes_referencia before running the pipeline). If this test fails, the
public helper has drifted from the internal derivation and HTTP/UI callers
will display a value that the pipeline rejects with PlanilhaInvalidaError.
"""

from pathlib import Path

import pytest

from app.application.pipeline import (
    _mes_referencia,
    derivar_mes_referencia_da_medicao,
)
from app.domain.errors import ArquivoNaoEncontradoError
from app.infrastructure import excel as writer

MEDICAO = Path(__file__).parent / 'fixtures' / 'medicao_mock.xlsx'


def test_derivar_mes_referencia_iguala_mes_referencia_interno():
    wb_ro, sheet_ro = writer.carregar_planilha(
        str(MEDICAO), read_only=True, data_only=True
    )
    try:
        col_map = writer.mapear_colunas(sheet_ro)
        (_i, _o, _d, _md, _sg,
         medicao_por_matricula, *_rest) = writer.indexar_e_ler_dados(sheet_ro, col_map)
    finally:
        wb_ro.close()
    esperado = _mes_referencia(medicao_por_matricula)
    obtido = derivar_mes_referencia_da_medicao(str(MEDICAO))
    assert obtido == esperado


def test_derivar_mes_referencia_arquivo_inexistente():
    with pytest.raises(ArquivoNaoEncontradoError):
        derivar_mes_referencia_da_medicao('/tmp/__nao_existe__.xlsx')
