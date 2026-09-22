"""Automation preview/apply logic extracted from pipeline_app/pages/3_Automatizar.py.

The functions prefixed with ``merge``/``filter``/``build_preview``/``apply_corrections``
preserve the exact semantics used by the Streamlit page (they are its source of
truth). The API layer adds type-safe ``build_changes`` / ``preview`` /
``apply_preview_changes``: they recompute the proposed corrections from the
current stored files every time (no data is trusted from the browser), only
touch whitelisted numeric fields, skip invalid/out-of-range OCR values, and
never modify ``fuente`` or the schematic metadata. Playwright / browser
automation is intentionally out of scope for this business workflow.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any

import pandas as pd

from automation_system.backend.deps import write_lock
from shared_store import db

# Presentation labels for the numeric fields corrected by automation.
FIELD_LABELS = {
    "superficie_m2": "Superficie",
    "capacidad_personas": "Capacidad",
    "plazas_estacionamiento": "Estacionamiento",
    "anio_construccion": "Año",
    "salas": "Salas",
}

# Validity bounds mirroring target_system.backend.schemas.PropertyUpdate: an OCR value
# outside these is considered invalid and skipped, never written.
FIELD_BOUNDS = {
    "superficie_m2": (0.0, 100_000.0),
    "capacidad_personas": (0, 100_000),
    "plazas_estacionamiento": (0, 100_000),
    "anio_construccion": (1900, 2100),
    "salas": (0, 100_000),
}


def merge_ocr_data(propiedades: pd.DataFrame, ocr: pd.DataFrame) -> pd.DataFrame:
    """Merge SIGE properties with OCR output (legacy vs ocr side by side)."""
    campos = db.NUMERIC_FIELDS
    return propiedades[["codigo", "direccion", "fuente"] + campos].merge(
        ocr[["codigo"] + campos], on="codigo", suffixes=("_legacy", "_ocr"), how="inner"
    )


def already_automated_codes(propiedades: pd.DataFrame) -> set[str]:
    """Codes whose source is already 'automatizacion OCR'."""
    return set(
        propiedades[propiedades["fuente"] == "automatizacion OCR"]["codigo"].astype(str)
    )


def filter_candidates(
    base: pd.DataFrame, ya_automatizadas: set[str], forzar: bool
) -> pd.DataFrame:
    """Restrict to candidates not yet automated (unless force is set)."""
    if forzar:
        return base
    return base[~base["codigo"].astype(str).isin(ya_automatizadas)]


def build_preview(candidatas: pd.DataFrame) -> list[dict]:
    """Rows for the 'Antes / despues' preview table."""
    campos = db.NUMERIC_FIELDS
    filas_preview: list[dict] = []
    for _, row in candidatas.iterrows():
        for campo in campos:
            legacy, ocr_val = row[f"{campo}_legacy"], row[f"{campo}_ocr"]
            if pd.isna(ocr_val):
                continue  # el OCR no pudo leer este campo: no se toca
            if str(legacy) != str(ocr_val):
                filas_preview.append({
                    "Codigo": row["codigo"], "Direccion": row["direccion"], "Campo": campo,
                    "Valor actual (legacy)": legacy, "Valor nuevo (OCR)": ocr_val,
                })
    return filas_preview


def apply_corrections(candidatas: pd.DataFrame, hoy: str | None = None) -> dict:
    """Apply OCR values into SIGE for every candidate. Returns summary counts."""
    campos = db.NUMERIC_FIELDS
    fecha = hoy if hoy is not None else date.today().strftime("%d/%m/%Y")
    corregidas, campos_corregidos = 0, 0
    for _, row in candidatas.iterrows():
        updates: dict = {}
        for campo in campos:
            ocr_val = row[f"{campo}_ocr"]
            if pd.isna(ocr_val):
                continue
            if str(row[f"{campo}_legacy"]) != str(ocr_val):
                updates[campo] = ocr_val
                campos_corregidos += 1
        if updates:
            updates["fuente"] = "automatizacion OCR"
            updates["ultima_actualizacion"] = fecha
            db.update_property(row["codigo"], updates)
            corregidas += 1
    return {"corregidas": corregidas, "campos_corregidos": campos_corregidos}


# --- API layer: type-safe preview / apply (recomputed from stored files) -----

def _clean_numeric(value: Any):
    """None para valores ausentes, no numericos o no finitos (OCR invalido)."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(num) or math.isinf(num):
        return None
    return num


def _equivalentes(a: Any, b: Any) -> bool:
    """563, 563.0 y '563' son equivalentes; 563 vs 588.2 no."""
    na, nb = _clean_numeric(a), _clean_numeric(b)
    if na is None and nb is None:
        return True
    if na is None or nb is None:
        return False
    return na == nb


def _en_rango(campo: str, valor: float) -> bool:
    lo, hi = FIELD_BOUNDS[campo]
    return lo <= valor <= hi


def _display(value: Any):
    """Valor numerico limpio para mostrar (int cuando no tiene decimales)."""
    num = _clean_numeric(value)
    if num is None:
        return None
    if isinstance(num, float) and num.is_integer():
        return int(num)
    return num


def build_changes(propiedades: pd.DataFrame, ocr: pd.DataFrame) -> list[dict]:
    """Correcciones propuestas por propiedad (OCR vs estado actual).

    Solo se proponen campos que existen en ambos datos, son numericos y
    validos (dentro de FIELD_BOUNDS) y difieren realmente del valor actual.
    Nunca toca codigo/direccion/fuente/ultima_actualizacion/metadatos.
    """
    merged = merge_ocr_data(propiedades, ocr)
    items: list[dict] = []
    for _, row in merged.iterrows():
        changes: list[dict] = []
        for campo in FIELD_LABELS:
            legacy = row.get(f"{campo}_legacy")
            ocr_val = row.get(f"{campo}_ocr")
            nuevo = _clean_numeric(ocr_val)
            if nuevo is None or not _en_rango(campo, nuevo):
                continue  # OCR invalido o fuera de rango: se salta con seguridad
            if _equivalentes(legacy, nuevo):
                continue
            changes.append({
                "field": campo,
                "label": FIELD_LABELS[campo],
                "current_value": _display(legacy),
                "new_value": _display(ocr_val),
            })
        if changes:
            items.append({
                "codigo": str(row["codigo"]),
                "direccion": row["direccion"],
                "changes": changes,
            })
    items.sort(key=lambda it: int(it["codigo"]) if it["codigo"].isdigit() else it["codigo"])
    return items


def preview() -> dict:
    """Resumen de correcciones propuestas; no modifica ningun dato."""
    propiedades = db.read_properties()
    ocr = db.read_ocr_output()
    if propiedades.empty or ocr.empty or "codigo" not in ocr.columns:
        return {
            "total_properties": len(propiedades),
            "properties_with_changes": 0,
            "total_changes": 0,
            "items": [],
        }
    items = build_changes(propiedades, ocr)
    return {
        "total_properties": len(propiedades),
        "properties_with_changes": len(items),
        "total_changes": sum(len(i["changes"]) for i in items),
        "items": items,
    }


def apply_preview_changes() -> dict:
    """Persiste las correcciones detectadas, recalculadas desde los archivos.

    No acepta valores del navegador: recalcula todo server-side y aplica solo
    campos validos. Idempotente: una segunda corrida no encuentra cambios.
    """
    propiedades = db.read_properties()
    ocr = db.read_ocr_output()
    if propiedades.empty or ocr.empty or "codigo" not in ocr.columns:
        return {"updated_properties": 0, "updated_fields": 0, "items": []}
    items = build_changes(propiedades, ocr)
    fecha = date.today().strftime("%d/%m/%Y")
    resultado: list[dict] = []
    updated_properties, updated_fields = 0, 0
    with write_lock():
        for it in items:
            updates = {c["field"]: c["new_value"] for c in it["changes"]}
            if not updates:
                continue
            try:
                db.update_property(it["codigo"], {**updates, "ultima_actualizacion": fecha})
            except ValueError:
                continue  # la propiedad desaparecio entre preview y apply: se salta
            resultado.append({"codigo": it["codigo"], "updated_fields": list(updates)})
            updated_properties += 1
            updated_fields += len(updates)
    return {
        "updated_properties": updated_properties,
        "updated_fields": updated_fields,
        "items": resultado,
    }