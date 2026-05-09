"""obter_mes_referencia_relatorio_treinamento: extrai mês da col 6, multi-mês erra."""

from __future__ import annotations

import io
from datetime import date

import openpyxl
import pytest

from app.domain.errors import PlanilhaInvalidaError
from app.infrastructure.data.bootstrap import (
    obter_mes_referencia_relatorio_treinamento,
)


def _xlsx_treinamento(rows: list[tuple]) -> bytes:
    """Gera xlsx com cabeçalho na linha 2 e dados a partir da linha 3.

    Schema espelha `loaders.carregar_dados_treinamento`: col 0=RE,
    col 1=nome, col 5=treinamento, col 6=data, col 7=carga.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["título", "ignorado"])
    ws.append(["RE", "Nome", "x", "y", "z", "Treinamento", "Data", "Carga"])
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_extrai_mes_quando_consistente(tmp_path):
    p = tmp_path / "t.xlsx"
    p.write_bytes(
        _xlsx_treinamento(
            [
                ("111", "Joao", "", "", "", "NR-10", date(2026, 3, 5), "8h"),
                ("222", "Maria", "", "", "", "NR-10", date(2026, 3, 15), "8h"),
            ]
        )
    )
    assert obter_mes_referencia_relatorio_treinamento(p) == "2026-03"


def test_levanta_em_multi_mes(tmp_path):
    p = tmp_path / "t.xlsx"
    p.write_bytes(
        _xlsx_treinamento(
            [
                ("111", "Joao", "", "", "", "NR-10", date(2026, 3, 5), "8h"),
                ("222", "Maria", "", "", "", "NR-10", date(2026, 4, 1), "8h"),
            ]
        )
    )
    with pytest.raises(PlanilhaInvalidaError) as exc:
        obter_mes_referencia_relatorio_treinamento(p)
    msg = str(exc.value)
    assert "2026-03" in msg
    assert "2026-04" in msg


def test_levanta_quando_nenhuma_data_valida(tmp_path):
    p = tmp_path / "t.xlsx"
    p.write_bytes(
        _xlsx_treinamento(
            [
                ("111", "Joao", "", "", "", "NR-10", None, "8h"),
            ]
        )
    )
    with pytest.raises(PlanilhaInvalidaError, match="sem datas"):
        obter_mes_referencia_relatorio_treinamento(p)
