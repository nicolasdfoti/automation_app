"""Schematic generation helpers extracted from pdf_creator/app_pdf_creator.py."""
from __future__ import annotations


def build_numeric_overrides(
    superficie_m2: float = 0.0,
    capacidad_personas: int = 0,
    plazas_estacionamiento: int = 0,
    anio_construccion: int = 0,
    salas: int = 0,
) -> dict:
    """Map form values to generator overrides: 0 means 'empty -> random'.

    Preserves the exact semantics of the original form: a value of 0 in any
    numeric field leaves it out so the generator draws it at random.
    """
    return {
        "superficie_m2": superficie_m2 or None,
        "capacidad_personas": int(capacidad_personas) or None,
        "plazas_estacionamiento": int(plazas_estacionamiento) or None,
        "anio_construccion": int(anio_construccion) or None,
        "salas": int(salas) or None,
    }