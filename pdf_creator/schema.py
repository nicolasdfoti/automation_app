"""
Campos que dibuja el esquematico. codigo y direccion NO se generan
aca: se toman de una propiedad que ya existe en target_system (via
shared_store), para garantizar que todo PDF generado corresponde a una
propiedad real del sistema.

derive_correct_values() es el corazon de la demo: a partir de los datos
ACTUALES (legacy/stale) de una propiedad, deriva los valores "correctos"
que va a dibujar el esquematico. La derivacion es DETERMINISTICA por
codigo (mismo codigo => mismo documento), los valores pertenecen a ESA
propiedad y difieren de los sembrados en campos seleccionados — que es
lo que la automatizacion va a corregir mas adelante.

El documento es la fuente de verdad: el PDF y el ground_truth guardan
exactamente estos valores; properties_db.xlsx conserva los datos stale
sin tocar hasta que la automatizacion los actualice.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: str
    unit: str = ""


NUMERIC_FIELDS = [
    Field("superficie_m2", "Superficie", "float", unit="m2"),
    Field("capacidad_personas", "Capacidad", "int", unit="pers."),
    Field("plazas_estacionamiento", "Plazas de estacionamiento", "int", unit="u."),
    Field("anio_construccion", "Ano de construccion", "int", unit=""),
    Field("salas", "Salas / ambientes", "int", unit="u."),
]

# Rango tipico de cada campo, usado solo cuando el valor actual es 0
# (nunca medido): el documento igual muestra un valor plausible.
_FRESH_RANGES = {
    "superficie_m2": (120.0, 1400.0),
    "capacidad_personas": (15, 350),
    "plazas_estacionamiento": (0, 90),
    "anio_construccion": (1955, 2023),
    "salas": (2, 24),
}


def hoy() -> str:
    return date.today().strftime("%d/%m/%Y")


def _semilla(codigo: str) -> int:
    """Semilla deterministica que ata los valores del documento AL codigo:
    el mismo codigo genera siempre el mismo documento."""
    if str(codigo).isdigit():
        return int(codigo)
    return sum(ord(c) for c in str(codigo))


def _no_cargado(valor) -> bool:
    return (
        valor is None
        or (isinstance(valor, float) and math.isnan(valor))
        or valor == 0
    )


def _corregido(field: Field, base, rng: random.Random):
    """Valor 'correcto' derivado del valor actual (stale). Los ajustes son
    deterministicos y plausibles: un relevamiento nuevo suele actualizar
    hacia arriba capacidad/superficie y ajustar ligeramente el resto."""
    if field.key == "superficie_m2":
        return round(float(base) * (1 + rng.uniform(0.01, 0.07)), 1)
    if field.key == "capacidad_personas":
        return int(base) + rng.randint(2, 12)
    if field.key == "plazas_estacionamiento":
        return int(base) + rng.randint(1, 5)
    if field.key == "anio_construccion":
        return max(1900, min(2023, int(base) + rng.randint(-2, 5)))
    if field.key == "salas":
        return int(base) + rng.randint(1, 4)
    return base


def _fresco(field: Field, rng: random.Random):
    lo, hi = _FRESH_RANGES[field.key]
    if field.kind == "float":
        return round(rng.uniform(lo, hi), 1)
    return rng.randint(lo, hi)


def derive_correct_values(legacy: dict, overrides: dict | None = None) -> dict:
    """Valores 'correctos' del esquematico derivados de los datos actuales
    de ESA propiedad. Si el usuario cargo algo puntual en la interfaz
    (overrides), se respeta; el resto se deriva deterministicamente del
    valor actual. Nunca modifica `legacy`."""
    overrides = overrides or {}
    codigo = str(legacy.get("codigo", ""))
    rng = random.Random(_semilla(codigo))
    valores = {}
    for field in NUMERIC_FIELDS:
        if field.key in overrides and overrides[field.key] not in (None, ""):
            valores[field.key] = overrides[field.key]
        elif _no_cargado(legacy.get(field.key)):
            valores[field.key] = _fresco(field, rng)
        else:
            valores[field.key] = _corregido(field, legacy[field.key], rng)
    return valores