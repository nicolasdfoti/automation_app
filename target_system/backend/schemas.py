"""Pydantic contracts for the Target System API responses and write payloads.

Field names mirror ``shared_store.db.PROPERTY_COLUMNS`` so the JSON contract
matches the existing Excel/data semantics. ``codigo`` is always a string.
Only the property-management models the Target System owns live here: no
automation, OCR, compare or schematics models.
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