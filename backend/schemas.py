"""Pydantic contracts for the read-only API responses.

Field names mirror ``shared_store.db.PROPERTY_COLUMNS`` so the JSON contract
matches the existing Excel/data semantics. ``codigo`` is always a string.
"""
from __future__ import annotations

from pydantic import BaseModel


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