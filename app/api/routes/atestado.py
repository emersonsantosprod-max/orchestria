"""POST /api/run/atestado

Fluxo: medicao + relatorio (xlsx atestado) → executar_pipeline (sem SQLite).
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.schemas.execution import ExecutionResult, InconsistenciaOut
from app.application.pipeline import executar_pipeline
from app.domain.errors import AutomacaoError
from app.infrastructure.paths import processed_output_path

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/api/run/atestado",
    response_model=ExecutionResult,
    status_code=status.HTTP_200_OK,
)
async def run_atestado(
    medicao: UploadFile,
    relatorio: UploadFile,
) -> ExecutionResult:
    medicao_bytes = await medicao.read()
    relatorio_bytes = await relatorio.read()

    tmp_medicao: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(medicao_bytes)
            tmp_medicao = tmp.name

        relatorio_fonte = io.BytesIO(relatorio_bytes)

        caminho_saida = str(processed_output_path("atestado"))

        logger.info("run_atestado: executando pipeline")
        resultado = executar_pipeline(
            caminho_medicao=tmp_medicao,
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
    finally:
        if tmp_medicao and os.path.exists(tmp_medicao):
            os.remove(tmp_medicao)

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
