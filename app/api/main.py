"""
api/main.py — FastAPI application.

Responsabilidades:
  - Criar o app FastAPI
  - Aplicar schema SQLite uma única vez no boot (lifespan)
  - Registrar todas as rotas /api/*
  - Servir ui/web/dist/ como StaticFiles (SPA React)

Regra: este módulo não contém lógica de negócio.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import config, initial_data, treinamentos
from app.infrastructure.data import conectar, create_schema
from app.infrastructure.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

_UI_DIST = Path(__file__).resolve().parents[2] / "ui" / "web" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bootstrap executado uma vez antes de aceitar requests."""
    conn = conectar()
    try:
        create_schema(conn)
        conn.commit()
    finally:
        conn.close()
    logger.info("api.lifespan: schema aplicado, pronto para servir")
    yield


app = FastAPI(
    title="Automação de Medição",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(initial_data.router)
app.include_router(config.router)
app.include_router(treinamentos.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if _UI_DIST.exists():
    app.mount("/", StaticFiles(directory=str(_UI_DIST), html=True), name="ui")
else:
    logger.warning("api.main: %s não encontrado — SPA não montada (rode `cd ui/web && npm run build`)", _UI_DIST)
