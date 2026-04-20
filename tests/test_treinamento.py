import pytest
from app import treinamento

def test_classificar_treinamento():
    tabela = {'TR-A': 'remunerado', 'TR-B': 'nao_remunerado'}
    assert treinamento.classificar_treinamento('TR-A', tabela) == 'remunerado'
    assert treinamento.classificar_treinamento('tr-a', tabela) == 'remunerado'
    with pytest.raises(KeyError):
        treinamento.classificar_treinamento('TR-C', tabela)

def test_calcular_desconto_nao_remunerado():
    # <= 9h10 -> desconto = nao_remunerado
    assert treinamento.calcular_desconto(8, 8) == 8
    # > 9h10 -> excesso = total - 9h10 -> max(0, nao_rem - excesso)
    # 10h total (todas não remuneradas). excesso = 10 - 9h10 = 50/60.
    # desc = 10 - 50/60 = 9 + 10/60 ≈ 9.1667
    assert round(treinamento.calcular_desconto(10, 10), 2) == 9.17

def test_calcular_desconto_misto():
    # 5 nao rem, 5 rem. Total 10. excesso = 50/60. desc = max(0, 5 - 50/60) ≈ 4.17
    assert round(treinamento.calcular_desconto(5, 10), 2) == 4.17
    # 2 nao rem, 8 rem. Total 10. excesso = 50/60. desc = max(0, 2 - 50/60) ≈ 1.17
    assert round(treinamento.calcular_desconto(2, 10), 2) == 1.17
    # 0 nao rem, 10 rem. Total 10. excesso = 50/60. desc = max(0, 0 - 50/60) = 0
    assert treinamento.calcular_desconto(0, 10) == 0

def test_expandir_datas():
    assert treinamento.expandir_datas('18/03/2026') == ['18/03/2026']
    assert treinamento.expandir_datas('18 À 19/03/2026') == ['18/03/2026', '19/03/2026']
    assert treinamento.expandir_datas('18 À 20/03/2026') == ['18/03/2026', '19/03/2026', '20/03/2026']
    
    with pytest.raises(ValueError):
        treinamento.expandir_datas('Data Invalida')

def test_montar_observacao():
    treinamentos = [{'nome': 'NR-10', 'horas': 8, 'remunerado': False}]
    obs = treinamento.montar_observacao(treinamentos, "")
    assert obs == "TREIN. NR-10 - 8H"

    # remunerado
    t_rem = [{'nome': 'NR-10', 'horas': 8, 'remunerado': True}]
    obs = treinamento.montar_observacao(t_rem, "")
    assert obs == "TREIN. NR-10 - 8H (NÃO DESCONTA)"

    # sem duplicar
    obs2 = treinamento.montar_observacao(treinamentos, "TREIN. NR-10 - 8H")
    assert obs2 == "TREIN. NR-10 - 8H"

def test_processar_fluxo_simples():
    dados = [{
        'linha': 1, 'matricula': '123', 'nome': 'A',
        'treinamento': 'TR', 'data': '18/03/2026', 'carga': '2H'
    }]
    tabela = {'TR': 'nao_remunerado'}
    atualizacoes, erros = treinamento.processar_treinamentos(dados, tabela, {})

    assert len(erros) == 0
    assert len(atualizacoes) == 1
    assert atualizacoes[0].matricula == '123'
    assert atualizacoes[0].desconto_min == 120  # 2 horas = 120 minutos
    assert atualizacoes[0].observacao == 'TREIN. TR - 2H'

def test_carga_zero_gera_erro_de_carga():
    dados = [{'linha': 1, 'matricula': '123', 'nome': 'A',
              'treinamento': 'TR', 'data': '18/03/2026', 'carga': '0H'}]
    tabela = {'TR': 'nao_remunerado'}
    atualizacoes, erros = treinamento.processar_treinamentos(dados, tabela, {})
    assert len(atualizacoes) == 0
    assert len(erros) == 1
    assert erros[0].erro == 'erro de carga'

def test_observacao_usa_nome_em_maiusculo():
    atualizacoes, erros = treinamento.processar_treinamentos(
        [{'linha': 1, 'matricula': '123', 'nome': 'A',
          'treinamento': 'nr-10', 'data': '18/03/2026', 'carga': '2H'}],
        {'NR-10': 'nao_remunerado'},
        {},
    )
    assert len(erros) == 0
    assert atualizacoes[0].observacao == 'TREIN. NR-10 - 2H'
