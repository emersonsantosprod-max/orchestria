"""Smoke + contrato de COLUMN_ALIASES."""

from app.domain.column_aliases import COLUMN_ALIASES, OBRIGATORIAS


def test_obrigatorias_presentes():
    for k in OBRIGATORIAS:
        assert k in COLUMN_ALIASES


def test_unidade_inclui_und_unid():
    assert COLUMN_ALIASES['unidade'] == ['unidade', 'und', 'unid']


def test_aliases_lowercase():
    for aliases in COLUMN_ALIASES.values():
        for a in aliases:
            assert a == a.lower()


def test_excel_mapear_colunas_consome_aliases():
    """mapear_colunas usa COLUMN_ALIASES como fonte única."""
    from openpyxl import Workbook

    from app.infrastructure import excel as writer

    wb = Workbook()
    ws = wb.active
    ws.append(['Data', 'RE', 'Descontos', 'Observação', 'Unidade'])
    col_map = writer.mapear_colunas(ws)
    assert 'unidade' in col_map
    assert col_map['unidade'] == 4
