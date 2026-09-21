"""Automation preview/apply logic extracted from pipeline_app/pages/3_Automatizar.py."""
from __future__ import annotations

from datetime import date

import pandas as pd

from shared_store import db


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