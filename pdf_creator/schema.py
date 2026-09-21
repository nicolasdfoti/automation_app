"""
Campos que dibuja el esquematico. codigo y direccion NO se generan
aca: se toman de una propiedad que ya existe en target_system (via
shared_store), para garantizar que todo PDF generado corresponde a una
propiedad real del sistema.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from typing import Callable


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: str
    random_fn: Callable[[], object]
    unit: str = ""


NUMERIC_FIELDS = [
    Field("superficie_m2", "Superficie", "float",
          lambda: round(random.uniform(120, 1400), 1), unit="m2"),
    Field("capacidad_personas", "Capacidad", "int",
          lambda: random.randint(15, 350), unit="pers."),
    Field("plazas_estacionamiento", "Plazas de estacionamiento", "int",
          lambda: random.randint(0, 90), unit="u."),
    Field("anio_construccion", "Ano de construccion", "int",
          lambda: random.randint(1955, 2023), unit=""),
    Field("salas", "Salas / ambientes", "int",
          lambda: random.randint(2, 24), unit="u."),
]


def hoy() -> str:
    return date.today().strftime("%d/%m/%Y")


def build_numeric_values(overrides: dict | None = None) -> dict:
    """Valores 'correctos' que va a mostrar el esquematico (el ground
    truth). Si el usuario cargo algo puntual en la interfaz, se respeta;
    el resto se completa al azar."""
    overrides = overrides or {}
    valores = {}
    for field in NUMERIC_FIELDS:
        if field.key in overrides and overrides[field.key] not in (None, ""):
            valores[field.key] = overrides[field.key]
        else:
            valores[field.key] = field.random_fn()
    return valores
