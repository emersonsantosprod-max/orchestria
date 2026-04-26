import os
from unittest.mock import patch

import openpyxl

from app import main
from app.infrastructure import db


def test_fluxo_completo(tmp_path):
    """
    Testa todo o ciclo usando apenas as fixtures geradas e valida
    a saída e a planilha final sem dependências externas reais.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    f_dir = os.path.join(base_dir, 'fixtures')

    medicao = os.path.join(f_dir, 'medicao_mock.xlsx')
    trein = os.path.join(f_dir, 'treinamentos_mock.xlsx')
    base_tr = os.path.join(f_dir, 'base_treinamentos_mock.xlsx')
    saida = str(tmp_path / "saida_mock.xlsx")
    db_file = str(tmp_path / "test.db")

    # Pre-populate bd_treinamentos so pipeline can resolve classification.
    conn_seed = db.conectar(db_file)
    db.registrar_base_treinamentos(base_tr, conn_seed)
    conn_seed.close()

    # definir_caminhos agora retorna 5 itens: (med, trein, saida, ferias, base_cob)
    with patch(
        'app.main.definir_caminhos',
        return_value=(medicao, trein, saida, '', ''),
    ), patch('app.infrastructure.db.conectar', return_value=db.conectar(db_file)):
        res = main.executar_medicao()

    # Devemos ter 3 registros processados com as fixtures ("TR-SIMPLES", "TR-REMUNERADO", "TR-MULTIDIA")
    assert res.processados == 3
    # User 111 teve 2 treinamentos no mesmo dia (agrupa em 1) e User 222 teve 1 em multi-dia (expande em 2). 1+2 = 3.
    assert res.atualizados == 3
    # Esperamos exatamente 1 aviso: medicao_mock não possui colunas
    # sg_funcao/md_cobranca/pct_cobranca, então validar_distribuicao=True
    # solicitada por main.executar_medicao é ignorada com aviso explícito.
    assert len(res.inconsistencias) == 1
    assert 'validar_distribuicao=True ignorado' in res.inconsistencias[0].erro

    # Validações internas do conteúdo salvo no Excel final
    wb = openpyxl.load_workbook(saida)
    ws = wb['Frequência']

    # As regras são: (desconto_min, max(0, nao_rem - excesso)) e string concats.
    # Linha 2 = RE 111 | 18/03 (TR-SIMPLES 2H nao rem, TR-REMUNERADO 8H rem) Total 10H.
    # Excesso 10H - 9h10 = 50/60 h. Desconto: max(0, 2H - 50/60) = 70/60 h = 1h10 (01:10)
    assert ws.cell(row=2, column=3).value == "TREIN. TR-SIMPLES - 2H; TREIN. TR-REMUNERADO - 8H (NÃO DESCONTA)"
    assert ws.cell(row=2, column=4).value == "01:10"

    # Linha 4 = RE 222 | 18/03 (TR-MULTIDIA 8H nao rem - Replicado pra cada dia segundo a regra)
    assert ws.cell(row=4, column=3).value == "TREIN. TR-MULTIDIA - 8H"
    assert ws.cell(row=4, column=4).value == "08:00"

    # Linha 5 = RE 222 | 19/03 (TR-MULTIDIA 8H nao rem - Replicado!)
    assert ws.cell(row=5, column=3).value == "TREIN. TR-MULTIDIA - 8H"
    assert ws.cell(row=5, column=4).value == "08:00"

    wb.close()
