"""Ports da camada application — Protocols por negócio.

Cada port carrega nome de negócio (TabelaClassificacao), nunca nome técnico
(Repository). Adapters concretos vivem em app/infrastructure/adapters/.
"""

from collections.abc import Mapping
from typing import Protocol


class TabelaClassificacao(Protocol):
    """Tabela nome-de-treinamento → tipo (ex.: NR-10, NR-35, GERAL).

    Usada por LancarTreinamentosService para classificar treinamentos lidos
    da planilha de Treinamentos Realizados.
    """

    def obter(self) -> Mapping[str, str]: ...
