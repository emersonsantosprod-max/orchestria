"""POST /api/config/{catalogo,medicao,cobranca,distribuicao}.

Cada endpoint recebe um xlsx via multipart, valida o parse, promove o
arquivo para storage durável (`data/uploads/<tipo>.xlsx`) via
`os.replace`, e registra o caminho em `registro_arquivos`.

Política de uploads corrompidos: o parse roda contra o arquivo temporário
ANTES do `os.replace`. Falha de validação descarta o tmp e preserva o
arquivo durável anterior intacto — registry permanece coerente.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.dependencies import get_conn
from app.api.schemas.config import (
    CatalogoUploadResponse,
    CobrancaUploadResponse,
    DistribuicaoUploadResponse,
    MedicaoUploadResponse,
)
from app.infrastructure.data import (
    DistribuicaoRepository,
    FeriasRepository,
    TreinamentosRepository,
    ler_medicao_do_excel,
    registrar_base_treinamentos,
    registrar_bd,
    registrar_cobranca,
    registrar_medicao_arquivo,
)
from app.infrastructure.data.bootstrap import _persistir_upload_permanente
from app.infrastructure.paths import uploads_dir

logger = logging.getLogger(__name__)
router = APIRouter()


async def _persistir_em_tmp(arquivo: UploadFile) -> str:
    """Grava o upload em arquivo temporário dentro de `uploads_dir()`.

    Mesmo filesystem do destino — pré-requisito para `os.replace` ser
    atômico no overwrite.
    """
    blob = await arquivo.read()
    with tempfile.NamedTemporaryFile(
        delete=False, suffix='.xlsx', dir=str(uploads_dir())
    ) as tmp:
        tmp.write(blob)
        return tmp.name


def _remover_se_existir(path: str | None) -> None:
    if path and os.path.exists(path):
        os.remove(path)


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
        durable = _persistir_upload_permanente(tmp_path, 'treinamentos')
        tmp_path = None
        registrar_base_treinamentos(durable, conn)
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
        _remover_se_existir(tmp_path)

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
        # Valida ANTES de promover para durável: se o Excel for inválido,
        # o storage durável anterior (se existir) permanece intacto.
        _, avisos = ler_medicao_do_excel(tmp_path)
        durable = _persistir_upload_permanente(tmp_path, 'medicao')
        tmp_path = None
        avisos, count = registrar_medicao_arquivo(durable, conn)
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
        _remover_se_existir(tmp_path)

    return MedicaoUploadResponse(
        count=count,
        arquivo=arquivo.filename or "",
        avisos=avisos,
    )


@router.post(
    "/api/config/cobranca",
    response_model=CobrancaUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_cobranca(
    arquivo: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> CobrancaUploadResponse:
    tmp_path: str | None = None
    try:
        tmp_path = await _persistir_em_tmp(arquivo)
        durable = _persistir_upload_permanente(tmp_path, 'cobranca')
        tmp_path = None
        registrar_cobranca(durable, conn)
        count = FeriasRepository(conn).count()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("upload_cobranca: falha ao registrar base de cobrança")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        _remover_se_existir(tmp_path)

    return CobrancaUploadResponse(count=count, arquivo=arquivo.filename or "")


@router.post(
    "/api/config/distribuicao",
    response_model=DistribuicaoUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_distribuicao(
    arquivo: UploadFile,
    conn: sqlite3.Connection = Depends(get_conn),
) -> DistribuicaoUploadResponse:
    tmp_path: str | None = None
    try:
        tmp_path = await _persistir_em_tmp(arquivo)
        durable = _persistir_upload_permanente(tmp_path, 'bd')
        tmp_path = None
        registrar_bd(durable, conn)
        count = DistribuicaoRepository(conn).count()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("upload_distribuicao: falha ao registrar bd_distribuicao")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        _remover_se_existir(tmp_path)

    return DistribuicaoUploadResponse(count=count, arquivo=arquivo.filename or "")
