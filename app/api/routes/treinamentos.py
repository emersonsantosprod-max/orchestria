"""POST /api/run/treinamentos

Fluxo:
  1. Recebe dois uploads: medicao (xlsx) + catalogo_treinamentos (xlsx)
  2. Salva medicao em NamedTemporaryFile — necessário para salvar_via_zip
  3. Passa catalogo como BytesIO direto para o loader
  4. Chama executar_pipeline via orquestração local (sem CLI)
  5. Remove temp após escrita; retorna ExecutionResult JSON

Restrições:
  - Nenhum arquivo persiste em disco além do output em saida_dir()
  - bd_treinamentos deve estar populado antes (catalog_status=READY)
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
from app.infrastructure.data import TreinamentosRepository
from app.infrastructure.paths import saida_dir

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/api/run/treinamentos",
    response_model=ExecutionResult,
    status_code=status.HTTP_200_OK,
)
async def run_treinamentos(
    medicao: UploadFile,
    catalogo: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> ExecutionResult:
    # Guard: catálogo precisa estar populado
    if TreinamentosRepository(conn).count() == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Catálogo de treinamentos não encontrado. "
                   "Faça upload do catálogo antes de executar.",
        )

    medicao_bytes = await medicao.read()
    catalogo_bytes = await catalogo.read()

    tmp_medicao: str | None = None
    try:
        # medicao → arquivo temporário (salvar_via_zip exige path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(medicao_bytes)
            tmp_medicao = tmp.name

        # catalogo → BytesIO (loaders.py aceita Fonte)
        catalogo_fonte = io.BytesIO(catalogo_bytes)

        destino = saida_dir()
        destino.mkdir(parents=True, exist_ok=True)
        caminho_saida = str(destino / "medicao_treinamentos_processada.xlsx")

        logger.info("run_treinamentos: executando pipeline")
        resultado = executar_pipeline(
            caminho_medicao=tmp_medicao,
            caminho_treinamentos=catalogo_fonte,
            caminho_saida=caminho_saida,
            conn=conn,
        )

    except Exception as exc:
        logger.exception("run_treinamentos: falha no pipeline")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        if tmp_medicao and os.path.exists(tmp_medicao):
            os.remove(tmp_medicao)

    return ExecutionResult(
        processados=resultado.processados,
        atualizados=resultado.atualizados,
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
