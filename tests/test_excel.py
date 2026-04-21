import openpyxl
import pytest

from app import excel as writer
from app.core import Update


def criar_planilha_mock(caminho):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Frequência'
    ws.append(['Data', 'RE', 'Observação', 'Descontos'])
    ws.append(['18/03/2026', '123', '', ''])
    wb.save(caminho)


def test_localizar_linhas_e_colunas(tmp_path):
    caminho = str(tmp_path / "teste_writer.xlsx")
    criar_planilha_mock(caminho)

    _, sheet = writer.carregar_planilha(caminho)
    col_map = writer.mapear_colunas(sheet)

    assert col_map['data'] == 0
    assert col_map['matricula'] == 1
    assert col_map['observacao'] == 2
    assert col_map['desconto'] == 3

    index = writer.indexar_e_ler_dados(sheet, col_map)[0]
    assert ('123', '18/03/2026') in index
    assert index[('123', '18/03/2026')] == [2]


def test_erro_matricula_nao_encontrada(tmp_path):
    caminho = str(tmp_path / "teste_writer_erro.xlsx")
    criar_planilha_mock(caminho)

    _, sheet = writer.carregar_planilha(caminho)
    col_map = writer.mapear_colunas(sheet)
    index = writer.indexar_e_ler_dados(sheet, col_map)[0]

    updates = [Update(
        tipo='treinamento',
        matricula='404',
        data='18/03/2026',
        observacao='T',
        desconto_min=0,
        sobrescrever_obs=True,
    )]

    _, erros = writer.aplicar_updates(updates, col_map, index)

    assert len(erros) == 1
    assert erros[0].matricula == '404'
    assert erros[0].erro == 'matrícula não encontrada'
    assert erros[0].origem == 'writer'


def test_mapear_ambiguidade_descontos(tmp_path):
    """Dois cabeçalhos que casariam com 'desconto' devem ser rejeitados."""
    caminho = str(tmp_path / "ambiguo.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Frequência'
    ws.append(['Data', 'RE', 'Descontos', 'Descontos Extras', 'Observação'])
    wb.save(caminho)

    _, sheet = writer.carregar_planilha(caminho)
    with pytest.raises(ValueError, match=r"\[MAPEAMENTO\] Ambiguidade"):
        writer.mapear_colunas(sheet)


def test_mapear_com_coluna_nova_no_meio(tmp_path):
    """Coluna nova inserida no meio (como Equipe em April) não quebra mapeamento."""
    caminho = str(tmp_path / "abril.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Frequência'
    ws.append(['Data', 'RE', 'Supervisor', 'Encarregado', 'Equipe', 'Ronda',
               'Apoio Calculo Descanso', 'Desconto Descanso', 'Descontos',
               'Observação', 'Total Descontos'])
    wb.save(caminho)

    _, sheet = writer.carregar_planilha(caminho)
    col_map = writer.mapear_colunas(sheet)

    assert col_map['data'] == 0
    assert col_map['matricula'] == 1
    assert col_map['desconto'] == 8
    assert col_map['observacao'] == 9
    assert col_map['_header_row'] == 1


def test_aplicar_updates_gera_patches(tmp_path):
    caminho = str(tmp_path / "teste_writer_sucesso.xlsx")
    criar_planilha_mock(caminho)

    _, sheet = writer.carregar_planilha(caminho)
    col_map = writer.mapear_colunas(sheet)
    index, _, descontos_existentes, *_ = writer.indexar_e_ler_dados(sheet, col_map)

    updates = [Update(
        tipo='treinamento',
        matricula='123',
        data='18/03/2026',
        observacao='NOVA OBS',
        desconto_min=120,
        sobrescrever_obs=True,
    )]

    patches, erros = writer.aplicar_updates(
        updates, col_map, index,
        descontos_existentes=descontos_existentes,
    )

    assert erros == []
    col_obs_1 = col_map['observacao'] + 1
    col_desc_1 = col_map['desconto'] + 1
    assert patches[(2, col_obs_1)] == 'NOVA OBS'
    assert patches[(2, col_desc_1)] == '02:00'
