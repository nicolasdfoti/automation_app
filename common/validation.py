"""Single source of truth for numeric field bounds and validation rules.

The bounds below mirror exactly what ``backend/schemas.py`` (PropertyUpdate)
and ``backend/services/automation.py`` (FIELD_BOUNDS) used independently.
Centralizing them here keeps both future applications consistent without
duplicating the literals.
"""
from __future__ import annotations

from common.models import NUMERIC_FIELDS

# (min, max) inclusive bounds for every numeric field. These are the
# canonical values; do not change them without updating the API schemas and
# the automation validation logic together.
FIELD_BOUNDS: dict[str, tuple[float | int, float | int]] = {
    "superficie_m2": (0.0, 100_000.0),
    "capacidad_personas": (0, 100_000),
    "plazas_estacionamiento": (0, 100_000),
    "anio_construccion": (1900, 2100),
    "salas": (0, 100_000),
}


def in_range(field: str, value: float | int) -> bool:
    """True when ``value`` falls within the canonical bounds of ``field``.

    Mirrors the semantics of automation's original ``_en_rango``: inclusive
    on both ends.
    """
    lo, hi = FIELD_BOUNDS[field]
    return lo <= value <= hi


def validate_numeric_field(field: str) -> None:
    """Raise KeyError for non-numeric field keys; no-op otherwise."""
    if field not in NUMERIC_FIELDS:
        raise KeyError(f"Campo no numerico: {field!r}. Numericos: {NUMERIC_FIELDS}")