"""Schematic generation helpers extracted from pdf_creator/app_pdf_creator.py."""
from __future__ import annotations

import math
from pathlib import Path

from backend.deps import write_lock
from backend.services import properties as properties_svc
from pdf_creator import generator
from shared_store import db


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


def list_pending() -> list[dict]:
    """Properties without a generated schematic, in the PendingSchematicItem shape."""
    pendientes = db.propiedades_pendientes_de_esquematico()
    items: list[dict] = []
    for _, row in pendientes.iterrows():
        superficie = row["superficie_m2"]
        items.append({
            "codigo": str(row["codigo"]),
            "direccion": row["direccion"] if not _is_na(row["direccion"]) else None,
            "superficie_m2": None if _is_na(superficie) else float(superficie),
            "estado": "pendiente",
        })
    return items


def generate_schematic(codigo: str, overrides: dict | None = None) -> dict:
    """Generate the schematic PDF for one property, serialized with the write lock."""
    with write_lock():
        path, record = generator.generate_for_property(codigo, overrides)
    return {
        "codigo": str(codigo),
        "archivo": path.name,
        "direccion": record["direccion"],
        "fecha_relevamiento": record["fecha_relevamiento"],
        "generado": True,
        "descargable": True,
    }


def generate_all_pending(overrides: dict | None = None) -> dict:
    """Generate schematics for every pending property.

    Individual failures are captured per-property without aborting the batch.
    """
    pendientes = db.propiedades_pendientes_de_esquematico()
    total = len(pendientes)
    generated = 0
    failed = 0
    results: list[dict] = []
    for codigo in pendientes["codigo"].astype(str):
        try:
            results.append(generate_schematic(codigo, overrides))
            generated += 1
        except Exception as exc:  # noqa: BLE001 - a single failure must not abort the batch
            failed += 1
            results.append({
                "codigo": codigo,
                "generado": False,
                "descargable": False,
                "error": str(exc),
            })
    return {
        "total": total,
        "generated": generated,
        "failed": failed,
        "results": results,
    }


def get_schematic_path(codigo: str) -> tuple[str, Path | None]:
    """Resolve the on-disk PDF for a property.

    Returns (status, path) where status is one of:
    "ok" | "property_not_found" | "no_schematic" | "file_missing".
    """
    record = properties_svc.get_property(codigo)
    if record is None:
        return "property_not_found", None
    archivo = record.get("archivo_esquematico")
    if not archivo:
        return "no_schematic", None
    path = db.SCHEMATICS_DIR / archivo
    if not path.exists():
        return "file_missing", None
    return "ok", path


def _is_na(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False