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


class InitialDataResponse(BaseModel):
    catalog_status: CatalogStatus
    measurement_status: MeasurementStatus
    report_status: ReportStatus
