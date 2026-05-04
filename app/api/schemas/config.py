"""Schemas de response para POST /api/config/*."""

from __future__ import annotations

from pydantic import BaseModel


class CatalogoUploadResponse(BaseModel):
    count: int
    arquivo: str


class MedicaoUploadResponse(BaseModel):
    count: int
    arquivo: str
    avisos: list[str]
