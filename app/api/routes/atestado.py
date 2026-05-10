"""POST /api/run/atestado

Fluxo: lê medição do registry (path absoluto) + recebe relatório xlsx via
multipart → executar_pipeline.
"""

from __future__ import annotations

import io
import logging
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.dependencies import get_conn
from app.api.schemas.execution import ExecutionResult, InconsistenciaOut
from app.application.pipeline import executar_pipeline
from app.domain.errors import AutomacaoError
from app.infrastructure.data import obter_medicao_atual
from app.infrastructure.paths import processed_output_path, validar_arquivo_referenciado

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolver_medicao_path(conn: sqlite3.Connection) -> str:
    rec = obter_medicao_atual(conn)
    if rec is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MEDICAO_NAO_REGISTRADA: registre a medição em Configurações.",
        )
    try:
        return str(validar_arquivo_referenciado(rec["caminho"], exts=(".xlsx", ".xls")))
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ARQUIVO_NAO_ENCONTRADO: {exc}",
        ) from exc
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/api/run/atestado",
    response_model=ExecutionResult,
    status_code=status.HTTP_200_OK,
)
async def run_atestado(
    relatorio: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> ExecutionResult:
    medicao_path = _resolver_medicao_path(conn)
    relatorio_bytes = await relatorio.read()

    try:
        relatorio_fonte = io.BytesIO(relatorio_bytes)
        caminho_saida = str(processed_output_path("atestado"))
        logger.info("run_atestado: executando pipeline")
        resultado = executar_pipeline(
            caminho_medicao=medicao_path,
            caminho_atestado=relatorio_fonte,
            caminho_saida=caminho_saida,
        )

    except HTTPException:
        raise
    except AutomacaoError as exc:
        logger.warning("run_atestado: erro de domínio: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("run_atestado: falha no pipeline")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno inesperado",
        ) from None

    return ExecutionResult(
        processados=resultado.atestados_processados,
        atualizados=resultado.atestados_atualizados,
        inconsistencias=[
            InconsistenciaOut(
                origem=str(inc.origem),
                linha=str(inc.linha),
                matricula=inc.matricula or "",
                data=inc.data or "",
                erro=inc.erro or "",
            )
            for inc in resultado.inconsistencias
        ],
        arquivo_saida=Path(resultado.caminho_saida).name,
    )
