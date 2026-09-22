"""Pydantic contracts for the Automation System API.

Field names mirror ``shared_store.db.PROPERTY_COLUMNS`` so the JSON contract
matches the existing Excel/data semantics. ``codigo`` is always a string.
Target-owned schemas (Property/PropertyList/Stats/PropertyUpdate) live in
``target_system/backend/schemas.py``; automation never imports them.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class PendingSchematicItem(BaseModel):
    codigo: str
    direccion: str | None = None
    superficie_m2: float | None = None
    estado: str = "pendiente"


class PendingSchematicList(BaseModel):
    count: int
    items: list[PendingSchematicItem]


class SchematicCatalogItem(BaseModel):
    """Estado de esquematico de una propiedad (pendiente o generado)."""

    codigo: str
    direccion: str | None = None
    superficie_m2: float | None = None
    esquematico_generado: bool
    archivo_esquematico: str | None = None


class SchematicCatalog(BaseModel):
    count: int
    items: list[SchematicCatalogItem]


class SchematicGenerateRequest(BaseModel):
    """Generation parameters for one property's schematic.

    Preserves the original form semantics: any numeric field left out (None)
    or set to 0 means "draw it at random".
    """

    codigo: str
    superficie_m2: float | None = Field(default=None, ge=0, le=100_000)
    capacidad_personas: int | None = Field(default=None, ge=0, le=100_000)
    plazas_estacionamiento: int | None = Field(default=None, ge=0, le=100_000)
    anio_construccion: int | None = Field(default=None, ge=0, le=2100)
    salas: int | None = Field(default=None, ge=0, le=100_000)


class SchematicResult(BaseModel):
    codigo: str
    archivo: str | None = None
    direccion: str | None = None
    fecha_relevamiento: str | None = None
    generado: bool = True
    descargable: bool = True
    error: str | None = None


class GenerateAllResult(BaseModel):
    total: int
    generated: int
    failed: int
    results: list[SchematicResult]


class OcrRunResult(BaseModel):
    """Synchronous result of one OCR pipeline execution."""

    status: str
    processed: int
    total: int


class OcrStatus(BaseModel):
    """Current state of the OCR output, derived from real stored data."""

    estado: str = "sin_esquematicos"
    total_esquematicos: int = 0
    procesados: int = 0
    pendientes: int = 0


class OcrResultItem(BaseModel):
    """One row of the stored OCR output (no internal implementation detail)."""

    codigo: str
    archivo: str | None = None
    direccion: str | None = None
    fecha_relevamiento: str | None = None
    superficie_m2: float | None = None
    capacidad_personas: int | None = None
    plazas_estacionamiento: int | None = None
    anio_construccion: int | None = None
    salas: int | None = None
    error: str | None = None


class OcrResultList(BaseModel):
    count: int
    items: list[OcrResultItem]


class CompareField(BaseModel):
    """Field-by-field outcome for one property, as produced by compute_comparison."""

    campo: str
    coinciden: bool | None = None
    ground_truth: float | int | None = None
    ocr: float | int | None = None


class CompareItem(BaseModel):
    codigo: str
    status: str
    todas_correctas: bool
    fields: list[CompareField]


class ComparePerField(BaseModel):
    campo: str
    exactitud: float


class CompareResponse(BaseModel):
    total: int
    coinciden: int
    diferencias: int
    sin_datos: int
    exactitud_global: float
    propiedades_con_error: int
    per_field: list[ComparePerField]
    items: list[CompareItem]


class AutomationChange(BaseModel):
    """One proposed field correction: current (stale) vs new (OCR) value."""

    field: str
    label: str
    current_value: float | int | None = None
    new_value: float | int | None = None


class AutomationItem(BaseModel):
    """Proposed corrections for a single property."""

    codigo: str
    direccion: str | None = None
    changes: list[AutomationChange]


class AutomationPreview(BaseModel):
    total_properties: int
    properties_with_changes: int
    total_changes: int
    items: list[AutomationItem]


class AutomationUpdatedItem(BaseModel):
    codigo: str
    updated_fields: list[str]


class AutomationApplyResult(BaseModel):
    updated_properties: int
    updated_fields: int
    items: list[AutomationUpdatedItem]


class PlaywrightAutomationRequest(BaseModel):
    """Request to automate ONE correction through the Target System UI.

    Only the property code and the field to correct are accepted; the value
    the browser writes is recomputed server-side from the stored files.
    """

    codigo: str
    field: str


class PlaywrightAutomationResult(BaseModel):
    """Detailed outcome of a single browser automation run.

    ``before_ui`` is the value the Target UI displayed before the update,
    while ``expected``/``after`` are the recomputed value and the value read
    back after saving. ``steps`` records what Playwright did, and ``stage``
    names the failing step when ``success`` is False (never a silent fallback).
    """

    success: bool
    codigo: str
    field: str
    before: float | int | None = None
    expected: float | int | None = None
    after: float | int | None = None
    verified: bool = False
    stage: str | None = None
    error: str | None = None
    steps: list[str] = []