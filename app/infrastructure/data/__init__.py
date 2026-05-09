"""
app/infrastructure/data — pacote de persistência SQLite.

Fachada pública (única superfície que callers importam):

    from app.infrastructure import data
    data.conectar(); data.create_schema(conn)
    data.registrar_bd(path, conn); data.obter_bd(conn)
    DistribuicaoRepository(conn), TreinamentosRepository(conn), ...

Regras:
  - Repositories: conn injetada, sem commit interno (caller controla transação).
  - bootstrap.*: orquestra xlsx → repo + commit (única camada que comita).
  - Schema: idempotente, criado no `conectar()` desta fachada.
  - Medição não é persistida em SQLite — `obter_medicao` re-lê o Excel
    durável apontado por `registro_arquivos['medicao']`.
"""

from __future__ import annotations

from app.infrastructure.data.bootstrap import (
    ler_medicao_do_excel,
    obter_bd,
    obter_cobranca,
    obter_medicao,
    obter_mes_referencia_excel,
    obter_registro_arquivos,
    obter_tabela_treinamento,
    popular_cobranca_se_vazio,
    registrar_base_treinamentos,
    registrar_bd,
    registrar_cobranca,
    registrar_medicao_arquivo,
)
from app.infrastructure.data.connection import conectar as _conectar_raw
from app.infrastructure.data.registry import RegistryRepository
from app.infrastructure.data.repositories.distribuicao import DistribuicaoRepository
from app.infrastructure.data.repositories.ferias import FeriasRepository
from app.infrastructure.data.repositories.treinamentos import TreinamentosRepository
from app.infrastructure.data.schema import create_schema


def conectar(path=None):
    """Abre conexão SQLite e garante schema idempotente."""
    conn = _conectar_raw(path)
    create_schema(conn)
    return conn


__all__ = [
    "conectar",
    "create_schema",
    "DistribuicaoRepository",
    "FeriasRepository",
    "TreinamentosRepository",
    "RegistryRepository",
    "registrar_bd",
    "registrar_medicao_arquivo",
    "registrar_base_treinamentos",
    "registrar_cobranca",
    "ler_medicao_do_excel",
    "obter_bd",
    "obter_medicao",
    "obter_mes_referencia_excel",
    "obter_cobranca",
    "obter_tabela_treinamento",
    "obter_registro_arquivos",
    "popular_cobranca_se_vazio",
]
