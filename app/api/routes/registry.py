"""POST /api/registry/{medicao,treinamentos,cobranca,distribuicao,tags}.

Path-based registration (4a). Cada endpoint recebe um JSON
`{"caminho": str}` com path absoluto do arquivo no host. Backend valida
existência/extensão/legibilidade via `validar_arquivo_referenciado`,
chama o loader correspondente (lendo do path original — sem cópia para
`data/uploads/`) e atualiza `registro_arquivos`.

Coexistência: rotas legadas em `app/api/routes/config.py` (UploadFile)
permanecem ativas durante a janela de migração. Removidas em commits
finais da Entrega 4a.
"""

from __future__ import annotations

import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_conn
from app.domain.errors import AutomacaoError
from app.infrastructure.data import (
    BaseTagsRepository,
    DistribuicaoRepository,
    FeriasRepository,
    TreinamentosRepository,
    registrar_base_tags,
    registrar_base_treinamentos,
    registrar_bd,
    registrar_cobranca,
)
from app.infrastructure.data.bootstrap import obter_mes_referencia_medicao_lite
from app.infrastructure.data.registry import RegistryRepository
from app.infrastructure.paths import validar_arquivo_referenciado

logger = logging.getLogger(__name__)
router = APIRouter()


class RegistryRequest(BaseModel):
    caminho: str = Field(..., min_length=1)


class RegistryMedicaoResponse(BaseModel):
    caminho: str
    mes_referencia: str
    avisos: list[str] = []


class RegistryBaseResponse(BaseModel):
    caminho: str
    qtd: int
    avisos: list[str] = []


def _validar_path(caminho: str, exts: tuple[str, ...]) -> str:
    try:
        return str(validar_arquivo_referenciado(caminho, exts=exts))
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
    "/api/registry/medicao",
    response_model=RegistryMedicaoResponse,
    status_code=status.HTTP_200_OK,
)
def registrar_medicao(
    payload: RegistryRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> RegistryMedicaoResponse:
    """Registra path da medição (lite). Só extrai mês via primeira data;
    validação completa (headers, multi-mês) ocorre apenas no Execute."""
    path = _validar_path(payload.caminho, exts=('.xlsx', '.xls'))
    try:
        mes = obter_mes_referencia_medicao_lite(path)
        RegistryRepository(conn).upsert('medicao', path)
        conn.commit()
    except (ValueError, AutomacaoError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return RegistryMedicaoResponse(caminho=path, mes_referencia=mes, avisos=[])


@router.post(
    "/api/registry/treinamentos",
    response_model=RegistryBaseResponse,
    status_code=status.HTTP_200_OK,
)
def registrar_treinamentos(
    payload: RegistryRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> RegistryBaseResponse:
    path = _validar_path(payload.caminho, exts=('.xlsx', '.xls'))
    try:
        registrar_base_treinamentos(path, conn)
        qtd = TreinamentosRepository(conn).count()
    except (ValueError, AutomacaoError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return RegistryBaseResponse(caminho=path, qtd=qtd)


@router.post(
    "/api/registry/cobranca",
    response_model=RegistryBaseResponse,
    status_code=status.HTTP_200_OK,
)
def registrar_cobranca_route(
    payload: RegistryRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> RegistryBaseResponse:
    path = _validar_path(payload.caminho, exts=('.xlsx', '.xls'))
    try:
        registrar_cobranca(path, conn)
        qtd = FeriasRepository(conn).count()
    except (ValueError, AutomacaoError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return RegistryBaseResponse(caminho=path, qtd=qtd)


@router.post(
    "/api/registry/distribuicao",
    response_model=RegistryBaseResponse,
    status_code=status.HTTP_200_OK,
)
def registrar_distribuicao(
    payload: RegistryRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> RegistryBaseResponse:
    path = _validar_path(payload.caminho, exts=('.xlsx', '.xls'))
    try:
        registrar_bd(path, conn)
        qtd = DistribuicaoRepository(conn).count()
    except (ValueError, AutomacaoError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return RegistryBaseResponse(caminho=path, qtd=qtd)


@router.post(
    "/api/registry/tags",
    response_model=RegistryBaseResponse,
    status_code=status.HTTP_200_OK,
)
def registrar_tags_route(
    payload: RegistryRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> RegistryBaseResponse:
    path = _validar_path(payload.caminho, exts=('.xlsx', '.xls'))
    try:
        registrar_base_tags(path, conn)
        qtd = BaseTagsRepository(conn).count()
    except (ValueError, AutomacaoError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return RegistryBaseResponse(caminho=path, qtd=qtd)


@router.get(
    "/api/registry/{tipo}",
    status_code=status.HTTP_200_OK,
)
def consultar_registry(
    tipo: str,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    """Lookup leve do registry para reidratação da UI."""
    rec = RegistryRepository(conn).get(tipo)
    if rec is None:
        return {"tipo": tipo, "registrado": False}
    return {"tipo": tipo, "registrado": True, **rec}
