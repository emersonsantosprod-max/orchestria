"""POST /api/run/distribuicao

Validação de aderência da medição contra bd_distribuicao. Sem geração de updates.
Guard: bd_distribuicao precisa estar populada (bootstrap em api.main.lifespan).
"""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.dependencies import get_conn
from app.api.schemas.execution import ExecutionResult, InconsistenciaOut
from app.application.pipeline import executar_pipeline
from app.infrastructure.data import DistribuicaoRepository
from app.infrastructure.paths import saida_dir

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/api/run/distribuicao",
    response_model=ExecutionResult,
    status_code=status.HTTP_200_OK,
)
async def run_distribuicao(
    medicao: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> ExecutionResult:
    if DistribuicaoRepository(conn).count() == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bd_distribuicao não populada. Verifique o bootstrap da aplicação.",
        )

    medicao_bytes = await medicao.read()

    tmp_medicao: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(medicao_bytes)
            tmp_medicao = tmp.name

        destino = saida_dir()
        destino.mkdir(parents=True, exist_ok=True)
        caminho_saida = str(destino / "medicao_distribuicao_processada.xlsx")

        logger.info("run_distribuicao: executando pipeline (validação)")
        resultado = executar_pipeline(
            caminho_medicao=tmp_medicao,
            caminho_saida=caminho_saida,
            conn=conn,
            validar_distribuicao=True,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("run_distribuicao: falha no pipeline")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        if tmp_medicao and os.path.exists(tmp_medicao):
            os.remove(tmp_medicao)

    return ExecutionResult(
        processados=0,
        atualizados=0,
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
