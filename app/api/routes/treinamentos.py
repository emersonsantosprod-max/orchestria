"""POST /api/run/treinamentos

Fluxo:
  1. Lê medição do registry (path absoluto registrado em Configurações)
  2. Recebe catálogo (xlsx) via multipart
  3. Valida coerência mês medição vs mês do relatório
  4. Chama executar_pipeline
  5. Retorna ExecutionResult JSON

Restrições:
  - Nenhum arquivo persiste em disco além do output em exports_dir()
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
from app.domain.errors import AutomacaoError
from app.infrastructure.data import TreinamentosRepository, obter_medicao_atual
from app.infrastructure.data.bootstrap import (
    obter_mes_referencia_medicao,
    obter_mes_referencia_relatorio_treinamento,
)
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
    "/api/run/treinamentos",
    response_model=ExecutionResult,
    status_code=status.HTTP_200_OK,
)
async def run_treinamentos(
    catalogo: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> ExecutionResult:
    if TreinamentosRepository(conn).count() == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Catálogo de treinamentos não encontrado. "
                   "Registre o catálogo antes de executar.",
        )

    medicao_path = _resolver_medicao_path(conn)
    catalogo_bytes = await catalogo.read()

    tmp_catalogo: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(catalogo_bytes)
            tmp_catalogo = tmp.name

        mes_medicao = obter_mes_referencia_medicao(medicao_path)
        mes_relatorio = obter_mes_referencia_relatorio_treinamento(tmp_catalogo)
        if mes_medicao != mes_relatorio:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Mês do relatório de treinamentos ({mes_relatorio}) "
                    f"difere do mês da medição ({mes_medicao})."
                ),
            )

        catalogo_fonte = io.BytesIO(catalogo_bytes)
        caminho_saida = str(processed_output_path("treinamentos"))

        logger.info("run_treinamentos: executando pipeline")
        resultado = executar_pipeline(
            caminho_medicao=medicao_path,
            caminho_treinamentos=catalogo_fonte,
            caminho_saida=caminho_saida,
            conn=conn,
        )

    except HTTPException:
        raise
    except AutomacaoError as exc:
        logger.warning("run_treinamentos: erro de domínio: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("run_treinamentos: falha no pipeline")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno inesperado",
        ) from None
    finally:
        if tmp_catalogo and os.path.exists(tmp_catalogo):
            os.remove(tmp_catalogo)

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
