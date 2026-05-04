"""POST /api/config/catalogo  e  POST /api/config/medicao.

Cada endpoint recebe um xlsx via multipart, persiste em SQLite e registra
em registro_arquivos. Após sucesso, GET /api/initial-data passa a retornar
CATALOG_READY / MEASUREMENT_READY conforme o caso.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.dependencies import get_conn
from app.api.schemas.config import CatalogoUploadResponse, MedicaoUploadResponse
from app.infrastructure.data import (
    MedicaoRepository,
    TreinamentosRepository,
    registrar_base_treinamentos,
    registrar_medicao,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _persistir_em_tmp(arquivo: UploadFile) -> str:
    blob = await arquivo.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(blob)
        return tmp.name


@router.post(
    "/api/config/catalogo",
    response_model=CatalogoUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_catalogo(
    arquivo: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> CatalogoUploadResponse:
    tmp_path: str | None = None
    try:
        tmp_path = await _persistir_em_tmp(arquivo)
        registrar_base_treinamentos(tmp_path, conn)
        count = TreinamentosRepository(conn).count()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("upload_catalogo: falha ao registrar catálogo")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return CatalogoUploadResponse(count=count, arquivo=arquivo.filename or "")


@router.post(
    "/api/config/medicao",
    response_model=MedicaoUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_medicao(
    arquivo: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> MedicaoUploadResponse:
    tmp_path: str | None = None
    try:
        tmp_path = await _persistir_em_tmp(arquivo)
        avisos = registrar_medicao(tmp_path, conn)
        count = MedicaoRepository(conn).count()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("upload_medicao: falha ao registrar medição")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return MedicaoUploadResponse(
        count=count,
        arquivo=arquivo.filename or "",
        avisos=avisos,
    )
