"""Validações novas em /api/config/{catalogo,cobranca}: 'sem dados' → 422."""

from __future__ import annotations

import io
import sqlite3

import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.infrastructure.data import conectar


@pytest.fixture
def client(tmp_path, monkeypatch):
    from app.api.dependencies import get_conn
    from app.api.main import app

    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr(
        "app.infrastructure.paths.uploads_dir", lambda: uploads
    )
    monkeypatch.setattr(
        "app.api.routes.config.uploads_dir", lambda: uploads
    )
    monkeypatch.setattr(
        "app.infrastructure.data.bootstrap.uploads_dir", lambda: uploads
    )

    db = tmp_path / "test.db"
    conectar(db).close()

    def _override():
        c = sqlite3.connect(str(db), timeout=5, check_same_thread=False)
        c.row_factory = sqlite3.Row
        try:
            yield c
        finally:
            c.close()

    app.dependency_overrides[get_conn] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        import logging
        for h in logging.root.handlers[:]:
            if getattr(h, "_automacao_file_handler", False):
                logging.root.removeHandler(h)
                h.close()


def _xlsx_vazio_apos_header(headers: list[str]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _xlsx_completamente_vazio() -> bytes:
    wb = openpyxl.Workbook()
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_upload_catalogo_sem_dados_retorna_422(client):
    """Catálogo lê min_row=2 → header sozinho equivale a vazio."""
    res = client.post(
        "/api/config/catalogo",
        files={"arquivo": ("vazio.xlsx", _xlsx_vazio_apos_header(["nome", "tipo"]))},
    )
    assert res.status_code == 422
    assert "sem dados" in res.json()["detail"].lower()


def test_upload_cobranca_sem_dados_retorna_422(client):
    """Cobrança não tem header — xlsx completamente vazio é a fonte de 'sem dados'."""
    res = client.post(
        "/api/config/cobranca",
        files={"arquivo": ("vazio.xlsx", _xlsx_completamente_vazio())},
    )
    assert res.status_code == 422
    assert "sem dados" in res.json()["detail"].lower()
