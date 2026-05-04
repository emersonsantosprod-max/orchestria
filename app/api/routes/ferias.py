"""POST /api/run/ferias

Fluxo: medicao + relatorio (xlsx férias) → executar_pipeline com cobranca via SQLite.
Guard: bd_cobranca precisa estar populada (bootstrap em api.main.lifespan).
"""

from __future__ import annotations

import io
import logging
import os
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.dependencies import get_conn
from app.api.schemas.execution import ExecutionResult, InconsistenciaOut
from app.application.pipeline import executar_pipeline
from app.infrastructure import data
from app.infrastructure.paths import saida_dir

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/api/run/ferias",
    response_model=ExecutionResult,
    status_code=status.HTTP_200_OK,
)
async def run_ferias(
    medicao: UploadFile,
    relatorio: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> ExecutionResult:
    if not data.obter_cobranca(conn):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bd_cobranca não populada. Verifique o bootstrap da aplicação.",
        )

    medicao_bytes = await medicao.read()
    relatorio_bytes = await relatorio.read()

    tmp_medicao: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(medicao_bytes)
            tmp_medicao = tmp.name

        relatorio_fonte = io.BytesIO(relatorio_bytes)

        destino = saida_dir()
        destino.mkdir(parents=True, exist_ok=True)
        caminho_saida = str(destino / "medicao_ferias_processada.xlsx")

        logger.info("run_ferias: executando pipeline")
        resultado = executar_pipeline(
            caminho_medicao=tmp_medicao,
            caminho_ferias=relatorio_fonte,
            caminho_saida=caminho_saida,
            conn=conn,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("run_ferias: falha no pipeline")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        if tmp_medicao and os.path.exists(tmp_medicao):
            os.remove(tmp_medicao)

    return ExecutionResult(
        processados=resultado.ferias_processadas,
        atualizados=resultado.ferias_atualizadas,
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
