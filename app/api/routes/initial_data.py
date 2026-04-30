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
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from app.api.dependencies import get_conn
from app.api.schemas.initial_data import (
    CatalogStatus,
    InitialDataResponse,
    MeasurementStatus,
    ReportStatus,
)
from app.infrastructure.data import RegistryRepository, TreinamentosRepository

router = APIRouter()


@router.get("/api/initial-data", response_model=InitialDataResponse)
def get_initial_data(conn: sqlite3.Connection = Depends(get_conn)) -> InitialDataResponse:
    treinamentos = TreinamentosRepository(conn)
    registry = RegistryRepository(conn)

    # catalog_status
    catalog_status = (
        CatalogStatus.READY
        if treinamentos.count() > 0
        else CatalogStatus.MISSING
    )

    # measurement_status
    medicao_reg = registry.get("medicao")
    measurement_status = (
        MeasurementStatus.READY
        if medicao_reg is not None
        else MeasurementStatus.MISSING
    )

    # report_status — ambos precisam estar prontos
    report_status = (
        ReportStatus.READY
        if catalog_status == CatalogStatus.READY
        and measurement_status == MeasurementStatus.READY
        else ReportStatus.MISSING
    )

    return InitialDataResponse(
        catalog_status=catalog_status,
        measurement_status=measurement_status,
        report_status=report_status,
    )
