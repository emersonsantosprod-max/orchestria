"""Schemas de request/response para GET /api/initial-data."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class CatalogStatus(str, Enum):
    READY = "CATALOG_READY"
    MISSING = "CATALOG_MISSING"


class MeasurementStatus(str, Enum):
    READY = "MEASUREMENT_READY"
    MISSING = "MEASUREMENT_MISSING"


class ReportStatus(str, Enum):
    READY = "REPORT_READY"
    MISSING = "REPORT_MISSING"


class ModuleStatus(BaseModel):
    enabled: bool
    reason: str | None = None


class ConfigStatus(BaseModel):
    ready: bool
    name: str | None = None
    saved_at: str | None = None


class InitialDataResponse(BaseModel):
    catalog_status: CatalogStatus
    measurement_status: MeasurementStatus
    report_status: ReportStatus
    mes_referencia: str | None = None
    modules: dict[str, ModuleStatus] = {}
    config: dict[str, ConfigStatus] = {}
    tables: dict[str, bool] = {}
