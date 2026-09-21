"""OCR vs ground-truth comparison, extracted from pipeline_app/pages/2_Comparar.py."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from shared_store import db


@dataclass
class ComparisonResult:
    resultado: pd.DataFrame     # one row per property: bool per field + todas_correctas
    merged: pd.DataFrame        # inner join ground_truth x ocr (for the side-by-side view)
    per_field: pd.DataFrame     # columns ["Campo", "Exactitud (%)"]
    exactitud_global: float
    propiedades_con_error: int


def compute_comparison(gt: pd.DataFrame, ocr: pd.DataFrame) -> ComparisonResult:
    """Compare OCR output against the known ground truth, field by field."""
    campos = db.NUMERIC_FIELDS
    merged = gt.merge(ocr, on="codigo", suffixes=("_gt", "_ocr"), how="inner")

    resultado = pd.DataFrame({"codigo": merged["codigo"]})
    total_comparaciones = 0
    total_correctas = 0
    for campo in campos:
        col_gt, col_ocr = f"{campo}_gt", f"{campo}_ocr"
        if col_gt not in merged or col_ocr not in merged:
            continue
        match = merged[col_gt].astype(str) == merged[col_ocr].astype(str)
        resultado[campo] = match
        total_comparaciones += len(match)
        total_correctas += int(match.sum())

    resultado["todas_correctas"] = resultado[campos].all(axis=1)
    exactitud_global = round(100 * total_correctas / total_comparaciones, 1) if total_comparaciones else 0.0
    propiedades_con_error = int((~resultado["todas_correctas"]).sum())

    per_field = pd.DataFrame({
        "Campo": campos,
        "Exactitud (%)": [round(100 * resultado[c].mean(), 1) for c in campos],
    })

    return ComparisonResult(
        resultado=resultado,
        merged=merged,
        per_field=per_field,
        exactitud_global=exactitud_global,
        propiedades_con_error=propiedades_con_error,
    )