"""B.1 — divergência multi-row em (matricula, data).

Quando o índice colapsa duas rows distintas para a mesma chave (matrícula,
data) mas as células de Observação ou Descontos diferem, last-write-wins na
indexação silenciaria a divergência. O writer agora emite warning quando um
Update de tipo='treinamento' (row=None) toca essa chave.
"""

import openpyxl

from app import excel as writer
from app.core import Update


def _criar_medicao_divergente(caminho: str) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Frequência'
    ws.append(['Data', 'RE', 'Observação', 'Descontos'])
    # Duas linhas com mesma (matricula, data) mas obs distintas
    ws.append(['18/03/2026', '111', 'NOTA A', None])
    ws.append(['18/03/2026', '111', 'NOTA B', None])
    wb.save(caminho)
    wb.close()


def test_indexar_detecta_obs_divergente(tmp_path):
    caminho = str(tmp_path / 'medicao.xlsx')
    _criar_medicao_divergente(caminho)
    wb, sheet = writer.carregar_planilha(caminho, read_only=True, data_only=True)
    col_map = writer.mapear_colunas(sheet)
    (_index, _obs, _desc, _mdc, _sg, _mpm, _records,
     obs_div, desc_div) = writer.indexar_e_ler_dados(sheet, col_map)
    wb.close()

    assert ('111', '18/03/2026') in obs_div
    assert ('111', '18/03/2026') not in desc_div


def test_aplicar_updates_emite_warning_em_treinamento_divergente():
    col_map = {
        'data': 0, 'matricula': 1, 'observacao': 2, 'desconto': 3,
        '_header_row': 1, '_ausentes': (),
    }
    index = {('111', '18/03/2026'): [2, 3]}
    obs_existentes = {('111', '18/03/2026'): 'NOTA B'}
    descontos_existentes = {('111', '18/03/2026'): 0}
    obs_div = {('111', '18/03/2026')}

    upd = Update(
        tipo='treinamento',
        matricula='111',
        data='18/03/2026',
        observacao='TREIN. TR-X - 2H',
        desconto_min=120,
        sobrescrever_obs=True,
        row=None,
    )

    _patches, incs = writer.aplicar_updates(
        [upd], col_map, index,
        obs_existentes=obs_existentes,
        descontos_existentes=descontos_existentes,
        obs_divergentes=obs_div,
    )

    erros = [i.erro for i in incs]
    assert any('divergente entre linhas duplicadas' in e for e in erros)
