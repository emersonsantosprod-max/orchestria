"""LancarTreinamentosService: wrapper behavior-preserving sobre gerar_updates_treinamento."""

from collections.abc import Mapping

from app.application.services.lancar_treinamentos import LancarTreinamentosService
from app.treinamento import gerar_updates_treinamento


class _FakeTabela:
    def __init__(self, mapping: Mapping[str, str]) -> None:
        self._mapping = mapping

    def obter(self) -> Mapping[str, str]:
        return self._mapping


def _dados_minimos():
    return [
        {
            'linha': 3,
            'matricula': '12345',
            'nome': 'TESTE',
            'treinamento': 'NR-10 BÁSICO',
            'data': '01/04/2026',
            'carga': '8H',
        },
    ]


def test_servico_devolve_mesmo_resultado_que_dominio_direto():
    tabela_map = {'NR-10 BÁSICO': 'NR-10'}
    dados = _dados_minimos()

    direto = gerar_updates_treinamento(dados, tabela_map, None)
    via_servico = LancarTreinamentosService(_FakeTabela(tabela_map)).executar(dados, None)

    assert direto == via_servico


def test_servico_propaga_observacoes_existentes():
    tabela_map = {'NR-35': 'NR-35'}
    dados = [
        {
            'linha': 4,
            'matricula': '99999',
            'nome': 'X',
            'treinamento': 'NR-35',
            'data': '02/04/2026',
            'carga': '4H',
        },
    ]
    obs = {('99999', '02/04/2026'): 'OBS PRÉ-EXISTENTE'}

    direto = gerar_updates_treinamento(dados, tabela_map, obs)
    via_servico = LancarTreinamentosService(_FakeTabela(tabela_map)).executar(dados, obs)

    assert direto == via_servico


def test_servico_consulta_tabela_uma_unica_vez():
    chamadas = []

    class _ContandoTabela:
        def obter(self):
            chamadas.append(1)
            return {'NR-10': 'NR-10'}

    LancarTreinamentosService(_ContandoTabela()).executar(_dados_minimos(), None)

    assert len(chamadas) == 1
