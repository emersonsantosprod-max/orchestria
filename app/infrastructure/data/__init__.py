"""
app/infrastructure/data — pacote de persistência SQLite.

Fachada pública (única superfície que callers importam):

    from app.infrastructure import data
    data.conectar(); data.create_schema(conn)
    data.registrar_bd(path, conn); data.obter_bd(conn)
    DistribuicaoRepository(conn), MedicaoRepository(conn), ...

Regras:
  - Repositories: conn injetada, sem commit interno (caller controla transação).
  - bootstrap.*: orquestra xlsx → repo + commit (única camada que comita).
  - Schema: idempotente, criado no `conectar()` desta fachada.
"""

from __future__ import annotations

from app.infrastructure.data.bootstrap import (
    obter_bd,
    obter_cobranca,
    obter_medicao,
    obter_registro_arquivos,
    obter_tabela_treinamento,
    popular_bd_se_vazio,
    popular_cobranca_se_vazio,
    popular_treinamentos_se_vazio,
    registrar_base_treinamentos,
    registrar_bd,
    registrar_cobranca,
    registrar_medicao,
)
from app.infrastructure.data.connection import conectar as _conectar_raw
from app.infrastructure.data.registry import RegistryRepository
from app.infrastructure.data.repositories.distribuicao import DistribuicaoRepository
from app.infrastructure.data.repositories.ferias import FeriasRepository
from app.infrastructure.data.repositories.medicao import MedicaoRepository
from app.infrastructure.data.repositories.treinamentos import TreinamentosRepository
from app.infrastructure.data.schema import create_schema
from app.infrastructure.paths import bundled_distribuicao_xlsx, bundled_treinamentos_xlsx


def conectar(path=None):
    """Abre conexão SQLite e garante schema idempotente."""
    conn = _conectar_raw(path)
    create_schema(conn)
    return conn


__all__ = [
    "conectar",
    "create_schema",
    "DistribuicaoRepository",
    "MedicaoRepository",
    "FeriasRepository",
    "TreinamentosRepository",
    "RegistryRepository",
    "registrar_bd",
    "registrar_medicao",
    "registrar_base_treinamentos",
    "registrar_cobranca",
    "obter_bd",
    "obter_medicao",
    "obter_cobranca",
    "obter_tabela_treinamento",
    "obter_registro_arquivos",
    "popular_bd_se_vazio",
    "popular_treinamentos_se_vazio",
    "popular_cobranca_se_vazio",
    "bundled_distribuicao_xlsx",
    "bundled_treinamentos_xlsx",
]
