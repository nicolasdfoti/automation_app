"""Pydantic contracts for the API responses and write payloads.

Field names mirror ``shared_store.db.PROPERTY_COLUMNS`` so the JSON contract
matches the existing Excel/data semantics. ``codigo`` is always a string.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class Property(BaseModel):
    codigo: str
    direccion: str
    superficie_m2: float
    capacidad_personas: int
    plazas_estacionamiento: int
    anio_construccion: int
    salas: int
    esquematico_generado: bool
    archivo_esquematico: str | None = None
    fuente: str
    ultima_actualizacion: str


class PropertyList(BaseModel):
    count: int
    items: list[Property]


class Stats(BaseModel):
    total: int
    pendientes: int
    corregidas: int
    superficie_total: float
    capacidad_total: int


class PropertyUpdate(BaseModel):
    """Editable fields of a property.

    Only the whitelisted business fields may be edited through the API.
    ``codigo`` stays the identifier and ``fuente``/``ultima_actualizacion``
    are system-managed.
    """

    direccion: str | None = Field(default=None, min_length=1, max_length=200)
    superficie_m2: float | None = Field(default=None, gt=0, le=100_000)
    capacidad_personas: int | None = Field(default=None, ge=0, le=100_000)
    plazas_estacionamiento: int | None = Field(default=None, ge=0, le=100_000)
    anio_construccion: int | None = Field(default=None, ge=1900, le=2100)
    salas: int | None = Field(default=None, ge=0, le=100_000)

    @field_validator("direccion")
    @classmethod
    def _strip_direccion(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("direccion no puede quedar vacia")
        return value

    @model_validator(mode="after")
    def _requires_at_least_one_field(self):
        if not self.model_dump(exclude_unset=True, exclude_none=True):
            raise ValueError("Se debe enviar al menos un campo para actualizar")
        return self


class PendingSchematicItem(BaseModel):
    codigo: str
    direccion: str | None = None
    superficie_m2: float | None = None
    estado: str = "pendiente"


class PendingSchematicList(BaseModel):
    count: int
    items: list[PendingSchematicItem]


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