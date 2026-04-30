"""Schemas de response para rotas POST /api/run/*."""

from __future__ import annotations

from pydantic import BaseModel


class InconsistenciaOut(BaseModel):
    origem: str
    linha: str
    matricula: str
    data: str
    erro: str


class ExecutionResult(BaseModel):
    processados: int
    atualizados: int
    inconsistencias: list[InconsistenciaOut]
    arquivo_saida: str  # nome do arquivo gerado em data/saida/
