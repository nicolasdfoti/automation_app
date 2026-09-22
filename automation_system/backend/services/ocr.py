"""OCR workflow orchestration.

The OCR algorithms stay in ``pipeline_app/ocr/pipeline_mock.py`` (the existing
source of truth). This service only orchestrates that implementation, mirrors
the exact persistence glue of its ``main()``, and exposes typed summaries.
"""
from __future__ import annotations

import math

import pandas as pd

from automation_system.backend.deps import write_lock
from pipeline_app.ocr import pipeline_mock as ocr_pipeline
from shared_store import db

# OCR output is shaped by pipeline_mock: codigo + archivo + the extracted fields.
OUTPUT_FIELDS = [
    "direccion", "fecha_relevamiento",
    "superficie_m2", "capacidad_personas", "plazas_estacionamiento",
    "anio_construccion", "salas",
]


def _is_na(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def _clean(value):
    return None if _is_na(value) else value


def codigos_procesados() -> set[str]:
    """Codes already present in ocr_output.xlsx (str-normalized, deduplicated)."""
    if not db.OCR_OUTPUT_XLSX.exists():
        return set()
    df = db.read_ocr_output()
    if df.empty or "codigo" not in df.columns:
        return set()
    return set(df["codigo"].dropna().astype(int).astype(str))


def run_ocr(reprocesar_todo: bool = False, workers: int = 1) -> dict:
    """Run the existing OCR pipeline and persist its output.

    Mirrors ``pipeline_mock.main()`` persistence (concat + drop_duplicates keep
    last). The stored-file behavior is preserved verbatim, including the known
    dtype quirk that can duplicate rows when a fresh run is merged over a file
    with a different codigo dtype. The API layer normalizes when *reading*,
    never when writing.
    """
    from shared_store import db as store

    omitir = [] if reprocesar_todo else sorted(codigos_procesados())
    df = ocr_pipeline.run_pipeline(
        db.SCHEMATICS_DIR, omitir_codigos=omitir, workers=workers
    )

    with write_lock():
        if df.empty:
            previo = db.read_ocr_output()
            return {
                "status": "completed",
                "processed": 0,
                "total": len(previo),
            }
        if db.OCR_OUTPUT_XLSX.exists():
            previo = pd.read_excel(db.OCR_OUTPUT_XLSX)
            combinado = pd.concat([previo, df], ignore_index=True).drop_duplicates("codigo", keep="last")
        else:
            combinado = df
        combinado.to_excel(db.OCR_OUTPUT_XLSX, index=False)

    return {
        "status": "completed",
        "processed": len(df),
        "total": len(combinado),
    }


def read_status() -> dict:
    """Real counters from stored data; no fabricated progress."""
    esquematicos = len(list(db.SCHEMATICS_DIR.glob("*.pdf"))) if db.SCHEMATICS_DIR.exists() else 0
    procesados = len(codigos_procesados())
    if esquematicos == 0:
        estado = "sin_esquematicos"
    elif not db.OCR_OUTPUT_XLSX.exists():
        estado = "nunca_ejecutado"
    else:
        estado = "completado"
    return {
        "estado": estado,
        "total_esquematicos": esquematicos,
        "procesados": procesados,
        "pendientes": max(esquematicos - procesados, 0),
    }


def read_results() -> list[dict]:
    """Typed rows from ocr_output.xlsx, deduplicated by codigo (keep last).

    Deduplication only affects the API response; the stored file is never
    rewritten here.
    """
    df = db.read_ocr_output()
    if df.empty:
        return []
    df = df.drop_duplicates("codigo", keep="last")
    items: list[dict] = []
    for _, row in df.iterrows():
        item: dict = {
            "codigo": str(row["codigo"]),
            "archivo": _clean(row.get("archivo")),
            "error": _clean(row.get("error")) if "error" in df.columns else None,
        }
        for campo in OUTPUT_FIELDS:
            if campo not in df.columns:
                item[campo] = None
                continue
            raw = row[campo]
            item[campo] = _clean(raw) if not _is_na(raw) else None
        items.append(item)
    return items