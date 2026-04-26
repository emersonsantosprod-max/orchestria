"""Use-case service: Lançar Treinamentos.

Coordena a leitura da tabela de classificação (via port) e a execução do
domínio puro (gerar_updates_treinamento). Não toca SQLite, não toca
openpyxl — depende apenas de Mapping retornado pelo port.
"""

from collections.abc import Mapping

from app.application.ports import TabelaClassificacao
from app.core import Inconsistencia, Update
from app.treinamento import gerar_updates_treinamento


class LancarTreinamentosService:
    def __init__(self, tabela: TabelaClassificacao) -> None:
        self._tabela = tabela

    def executar(
        self,
        dados: list,
        observacoes_existentes: Mapping | None = None,
    ) -> tuple[list[Update], list[Inconsistencia]]:
        return gerar_updates_treinamento(dados, self._tabela.obter(), observacoes_existentes)
