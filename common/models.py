"""Canonical shared domain definitions for the Automation Suite.

This is the single source of truth for property/domain concepts used by both
the Target System and the Automation System:

- ``PROPERTY_COLUMNS`` and ``NUMERIC_FIELDS``: the workbook/row contract
  (previously duplicated in ``shared_store/db.py``).
- ``Field`` + ``FIELD_DEFS``: the numeric fields a schematic draws and the
  data shared with ground truth / OCR output (canonical form of the defs in
  ``pdf_creator/schema.py``).
- ``FIELD_LABELS``: short presentation labels used in previews/automation
  (canonical form of ``backend/services/automation.py``'s dict).

No application imports here; only the standard library.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    """A numeric business field present in a property row and a schematic."""

    key: str
    label: str
    kind: str
    unit: str = ""


# Full row contract of properties_db.xlsx.
PROPERTY_COLUMNS = [
    "codigo",
    "direccion",
    "superficie_m2",
    "capacidad_personas",
    "plazas_estacionamiento",
    "anio_construccion",
    "salas",
    "esquematico_generado",
    "archivo_esquematico",
    "fuente",
    "ultima_actualizacion",
]

# The numeric fields automation can validate/correct and schematics draw.
NUMERIC_FIELDS = [
    "superficie_m2",
    "capacidad_personas",
    "plazas_estacionamiento",
    "anio_construccion",
    "salas",
]

# Detailed field definitions (key/label/kind/unit), canonical form of the
# list that pdf_creator/schema.py uses to draw schematics. Kind is "float"
# for superficie_m2 and "int" for the rest.
FIELD_DEFS: tuple[Field, ...] = (
    Field("superficie_m2", "Superficie", "float", unit="m2"),
    Field("capacidad_personas", "Capacidad", "int", unit="pers."),
    Field("plazas_estacionamiento", "Plazas de estacionamiento", "int", unit="u."),
    Field("anio_construccion", "Ano de construccion", "int", unit=""),
    Field("salas", "Salas / ambientes", "int", unit="u."),
)

# Short presentation labels shown by the automation previews.
FIELD_LABELS: dict[str, str] = {
    "superficie_m2": "Superficie",
    "capacidad_personas": "Capacidad",
    "plazas_estacionamiento": "Estacionamiento",
    "anio_construccion": "Año",
    "salas": "Salas",
}

_FIELD_DEFS_BY_KEY = {f.key: f for f in FIELD_DEFS}


def field_def(key: str) -> Field:
    """Return the canonical Field definition for a numeric field key."""
    return _FIELD_DEFS_BY_KEY[key]