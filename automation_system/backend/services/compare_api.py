"""OCR vs ground-truth comparison, exposing the existing compute_comparison.

The matching algorithm, field names, difference and status semantics all come
from ``backend/services/compare.py`` (the source of truth previously used by
pipeline_app/pages/2_Comparar.py). This service only translates its outputs
into a typed JSON shape and enumerates codes present in ground truth but not
in OCR output (the UI's "sin datos" case).
"""
from __future__ import annotations

import math

from automation_system.backend.services.compare import compute_comparison
from shared_store import db


def _is_na(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def _clean(value):
    return None if _is_na(value) else value


def _norm_codes(series) -> set[str]:
    return set(series.dropna().astype(int).astype(str))


def compare_summary() -> dict:
    gt = db.read_ground_truth()
    ocr = db.read_ocr_output()

    campos = db.NUMERIC_FIELDS
    if gt.empty or ocr.empty:
        sin_datos = len(gt) if ocr.empty else 0
        return {
            "total": 0,
            "coinciden": 0,
            "diferencias": 0,
            "sin_datos": sin_datos,
            "exactitud_global": 0.0,
            "propiedades_con_error": 0,
            "per_field": [],
            "items": [],
        }

    comparacion = compute_comparison(gt, ocr)
    resultado, merged = comparacion.resultado, comparacion.merged

    merged_by_codigo = merged.set_index(merged["codigo"].astype(int).astype(str))
    items: list[dict] = []

    for _, row in resultado.iterrows():
        codigo = str(int(row["codigo"]))
        mrow = merged_by_codigo.loc[codigo] if codigo in merged_by_codigo.index else None
        fields: list[dict] = []
        for campo in campos:
            col_gt, col_ocr = f"{campo}_gt", f"{campo}_ocr"
            if col_gt not in merged.columns or col_ocr not in merged.columns:
                continue
            coinciden = bool(row[campo])
            if mrow is None:
                gt_val = ocr_val = None
            else:
                gt_val = _clean(mrow[col_gt])
                ocr_val = _clean(mrow[col_ocr])
            fields.append({
                "campo": campo,
                "coinciden": coinciden,
                "ground_truth": gt_val,
                "ocr": ocr_val,
            })
        items.append({
            "codigo": codigo,
            "status": "coincide" if bool(row["todas_correctas"]) else "diferencia",
            "todas_correctas": bool(row["todas_correctas"]),
            "fields": fields,
        })

    gt_codes = _norm_codes(gt["codigo"])
    ocr_codes = _norm_codes(ocr["codigo"])
    sin_datos_codes = sorted(gt_codes - ocr_codes, key=int)

    gt_by_codigo = gt.set_index(gt["codigo"].astype(int).astype(str))
    for codigo in sin_datos_codes:
        grep = gt_by_codigo.loc[codigo]
        items.append({
            "codigo": codigo,
            "status": "sin_datos",
            "todas_correctas": False,
            "fields": [
                {
                    "campo": campo,
                    "coinciden": None,
                    "ground_truth": _clean(grep[campo]),
                    "ocr": None,
                }
                for campo in campos
                if campo in grep.index
            ],
        })

    items.sort(key=lambda item: int(item["codigo"]) if item["codigo"].isdigit() else item["codigo"])

    coinciden = int(resultado["todas_correctas"].sum())
    return {
        "total": len(resultado),
        "coinciden": coinciden,
        "diferencias": int(comparacion.propiedades_con_error),
        "sin_datos": len(sin_datos_codes),
        "exactitud_global": comparacion.exactitud_global,
        "propiedades_con_error": comparacion.propiedades_con_error,
        "per_field": [
            {"campo": str(row["Campo"]), "exactitud": float(row["Exactitud (%)"])}
            for _, row in comparacion.per_field.iterrows()
        ],
        "items": items,
    }