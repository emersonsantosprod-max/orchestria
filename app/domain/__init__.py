"""Camada de domínio: funções puras + dataclasses.

Re-exports ergonômicos para os tipos compartilhados mais usados.
"""

from app.domain.core import (
    LIMITE_HORAS_TRABALHADAS,
    Inconsistencia,
    Update,
    deduplicar_observacao,
    inconsistencia,
    normalizar_matricula,
)

__all__ = [
    "LIMITE_HORAS_TRABALHADAS",
    "Inconsistencia",
    "Update",
    "deduplicar_observacao",
    "inconsistencia",
    "normalizar_matricula",
]
