"""GET /api/initial-data — estado inicial consumido pelo ViewModel React.

Lógica de derivação (espelho do flowchart Mermaid):

  catalog_status:
    READY   → bd_treinamentos tem dados
    MISSING → tabela vazia

  measurement_status:
    READY   → registro_arquivos tem entrada 'medicao' com caminho válido
    MISSING → ausente ou caminho inválido

  report_status:
    READY   → CATALOG_READY AND MEASUREMENT_READY
    MISSING → qualquer um dos dois ausente

  modules:
    Por id (treinamentos, ferias, atestados, validar-hr, validar-dist) — cada um
    expõe enabled/reason derivados das tabelas reais para guiar o gating de UI.

  config:
    base_treinamentos / bd_distribuicao — refletem dados persistidos em SQLite.
    base_cobranca permanece efêmero (não persistido) → ready=false.

  tables:
    Presença bruta de catalogo_treinamentos e bd_distribuicao em sqlite_master
    — usado pelo log de bootstrap da UI. Medição não é mais persistida em
    SQLite; sua disponibilidade é avaliada via registro_arquivos.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends

from app.api.dependencies import get_conn
from app.api.schemas.initial_data import (
    CatalogStatus,
    ConfigStatus,
    InitialDataResponse,
    MeasurementStatus,
    ModuleStatus,
    ReportStatus,
)
from app.infrastructure.data import (
    DistribuicaoRepository,
    RegistryRepository,
    TreinamentosRepository,
    obter_mes_referencia_excel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


_TRACKED_TABLES = ("catalogo_treinamentos", "bd_distribuicao")


def _tabelas_presentes(conn: sqlite3.Connection) -> dict[str, bool]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    presentes = {r[0] for r in rows}
    return {t: t in presentes for t in _TRACKED_TABLES}


def _derivar_mes_referencia(caminho: str) -> str | None:
    try:
        return obter_mes_referencia_excel(Path(caminho))
    except FileNotFoundError:
        logger.error(
            "Arquivo de medição registrado ausente em disco: %s", caminho
        )
        return None
    except Exception:
        logger.exception(
            "Falha ao derivar mes_referencia do Excel registrado: %s", caminho
        )
        return None


@router.get("/api/initial-data", response_model=InitialDataResponse)
def get_initial_data(conn: sqlite3.Connection = Depends(get_conn)) -> InitialDataResponse:
    treinamentos = TreinamentosRepository(conn)
    registry = RegistryRepository(conn)

    catalog_ready = treinamentos.count() > 0
    catalog_status = CatalogStatus.READY if catalog_ready else CatalogStatus.MISSING

    medicao_reg = registry.get("medicao")
    measurement_ready = medicao_reg is not None and Path(medicao_reg["caminho"]).exists()
    measurement_status = (
        MeasurementStatus.READY if measurement_ready else MeasurementStatus.MISSING
    )

    report_status = (
        ReportStatus.READY
        if catalog_ready and measurement_ready
        else ReportStatus.MISSING
    )

    mes_referencia = (
        _derivar_mes_referencia(medicao_reg["caminho"]) if measurement_ready else None
    )

    distribuicao_ready = DistribuicaoRepository(conn).count() > 0

    def _module(enabled: bool, reason: str | None) -> ModuleStatus:
        return ModuleStatus(enabled=enabled, reason=None if enabled else reason)

    sem_medicao = "Carregue a medição para liberar este módulo."
    modules = {
        "treinamentos": _module(
            catalog_ready and measurement_ready,
            "Importe a base de treinamentos em Configuração."
            if not catalog_ready
            else sem_medicao,
        ),
        "ferias": _module(measurement_ready, sem_medicao),
        "atestados": _module(measurement_ready, sem_medicao),
        "validar-hr": _module(measurement_ready, sem_medicao),
        "validar-dist": _module(
            measurement_ready and distribuicao_ready,
            "BD Distribuição não carregado."
            if not distribuicao_ready
            else sem_medicao,
        ),
    }

    bd_reg = registry.get("bd")
    base_tre_reg = registry.get("treinamentos")

    config = {
        "base_cobranca": ConfigStatus(ready=False, name=None, saved_at=None),
        "base_treinamentos": ConfigStatus(
            ready=catalog_ready,
            name=base_tre_reg["caminho"] if base_tre_reg else None,
            saved_at=base_tre_reg["importado_em"] if base_tre_reg else None,
        ),
        "bd_distribuicao": ConfigStatus(
            ready=distribuicao_ready,
            name=bd_reg["caminho"] if bd_reg else None,
            saved_at=bd_reg["importado_em"] if bd_reg else None,
        ),
    }

    return InitialDataResponse(
        catalog_status=catalog_status,
        measurement_status=measurement_status,
        report_status=report_status,
        mes_referencia=mes_referencia,
        modules=modules,
        config=config,
        tables=_tabelas_presentes(conn),
    )
