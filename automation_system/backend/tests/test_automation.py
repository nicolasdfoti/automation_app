"""Backend test battery for the automation preview workflow.

Run with the project venv:

    venv/Scripts/python.exe -m automation_system.backend.tests.test_automation

Follows the project's inline test-battery convention (no pytest dependency).
The shared_store workbooks are snapshotted first and restored unconditionally
in ``finally``, so the test works against a controlled state and never
permanently alters the baseline dataset.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from automation_system.backend.services.automation import (  # noqa: E402
    FIELD_BOUNDS,
    _clean_numeric,
    _display,
    _equivalentes,
    build_changes,
    preview,
)
from shared_store import db  # noqa: E402

FIELDS = db.NUMERIC_FIELDS
SNAPSHOT_DIR = Path(os.environ["TEMP"]) / f"automation_test_{os.getpid()}"


def _perturbar(actual: object, lo: int, hi: int, field: str) -> float | int:
    """Valor distinto del actual (stale), dentro de los limites validos."""
    cur = float(actual)
    if field == "superficie_m2":
        v = cur * 0.9
    elif field == "capacidad_personas":
        v = cur - 7 if cur - 7 > lo else cur + 7
    elif field == "plazas_estacionamiento":
        v = cur + 3 if cur + 3 < hi else cur - 3
    elif field == "anio_construccion":
        v = cur - 15 if cur - 15 >= lo else cur + 15
    else:  # salas
        v = cur + 2 if cur + 2 < hi else cur - 2
    if field != "superficie_m2":
        return int(v)
    return round(v, 1)


def seed_stale() -> pd.DataFrame:
    """Construye un estado stale controlado: todos los campos difieren del OCR."""
    props = db.read_properties()
    for _, row in props.iterrows():
        codigo = str(int(row["codigo"]))
        updates = {}
        for field in FIELDS:
            new = _perturbar(row[field], *FIELD_BOUNDS[field], field)
            assert not _equivalentes(new, row[field]), (codigo, field)  # garante bien diferencia
            updates[field] = new
        db.update_property(codigo, updates)
    return db.read_properties()


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    for f in (db.PROPERTIES_XLSX, db.GROUND_TRUTH_XLSX, db.OCR_OUTPUT_XLSX):
        shutil.copy2(f, SNAPSHOT_DIR / f.name)
    pdfs = SNAPSHOT_DIR / "schematics"
    pdfs.mkdir(exist_ok=True)
    for pdf in db.SCHEMATICS_DIR.glob("*.pdf"):
        shutil.copy2(pdf, pdfs / pdf.name)


def restore() -> None:
    for f in (db.PROPERTIES_XLSX, db.GROUND_TRUTH_XLSX, db.OCR_OUTPUT_XLSX):
        shutil.copy2(SNAPSHOT_DIR / f.name, f)
    for pdf in db.SCHEMATICS_DIR.glob("*.pdf"):
        pdf.unlink()
    for pdf in (SNAPSHOT_DIR / "schematics").glob("*.pdf"):
        shutil.copy2(pdf, db.SCHEMATICS_DIR / pdf.name)
    print("[restore] shared_store restaurado al snapshot")


def run_checks() -> None:
    props0 = seed_stale()
    ocr0 = db.read_ocr_output()
    assert not props0.empty and not ocr0.empty
    # el estado stale semeado garantiza que hay correcciones pendientes
    p_seed = preview()
    assert p_seed["total_properties"] == len(props0)
    assert p_seed["total_changes"] >= len(props0)  # al menos un campo por propiedad

    # --- type handling: no false differences por representacion ---
    assert _equivalentes(563, "563")
    assert _equivalentes(563.0, 563)
    assert _equivalentes("563.0", 563)
    assert not _equivalentes(563, 588.2)
    assert _equivalentes(None, None)
    assert not _equivalentes(None, 5)
    assert _clean_numeric(float("nan")) is None
    assert _clean_numeric("abc") is None
    assert _clean_numeric("") is None
    assert _display(563.0) == 563
    assert _display(588.2) == 588.2
    print("[ok] manejo de tipos (int/float/str/NaN)")

    # --- preview: estado stale -> correccion propuesta ---
    p = preview()
    assert p["total_properties"] == len(props0)
    assert p["properties_with_changes"] > 0
    assert p["total_changes"] > 0
    assert len(p["items"]) == p["properties_with_changes"]
    assert p["total_changes"] == sum(len(i["changes"]) for i in p["items"])
    for item in p["items"]:
        assert item["codigo"]
        assert len({c["field"] for c in item["changes"]}) == len(item["changes"])  # sin duplicados
        for c in item["changes"]:
            assert c["field"] in FIELDS
            assert c["label"]
            assert not _equivalentes(c["current_value"], c["new_value"])
    print(f"[ok] preview: {p['properties_with_changes']} propiedades, {p['total_changes']} campos")

    # --- datos invalidos (solo lectura, sobre el estado stale) ----------------
    ocr_norm_all = ocr0.drop_duplicates("codigo", keep="last")
    prop_codes = set(props0["codigo"].astype(str))
    shared_codes = [str(c) for c in ocr_norm_all["codigo"] if str(c) in prop_codes]
    assert shared_codes, "no hay propiedad compartida entre properties_db y ocr_output"
    codigo = shared_codes[0]
    ocr_bad = ocr_norm_all.copy()
    ocr_bad["superficie_m2"] = ocr_bad["superficie_m2"].astype(object)
    ocr_bad.loc[ocr_bad["codigo"].astype(str) == codigo, "superficie_m2"] = "no-valido"
    ocr_bad.loc[ocr_bad["codigo"].astype(str) == codigo, "anio_construccion"] = 3000  # fuera de rango
    ocr_bad.loc[ocr_bad["codigo"].astype(str) == codigo, "plazas_estacionamiento"] = None
    ocr_bad.to_excel(db.OCR_OUTPUT_XLSX, index=False)

    p_bad = preview()
    item_bad = next(i for i in p_bad["items"] if i["codigo"] == codigo)  # sigue teniendo correcciones validas
    campos_bad = {c["field"] for c in item_bad["changes"]}
    assert "superficie_m2" not in campos_bad
    assert "anio_construccion" not in campos_bad
    assert "plazas_estacionamiento" not in campos_bad
    assert campos_bad <= set(FIELDS)
    print("[ok] datos invalidos omitidos en preview (no se proponen)")

    # --- volver al OCR preseteado para continuar el flujo limpio --------------
    shutil.copy2(SNAPSHOT_DIR / db.OCR_OUTPUT_XLSX.name, db.OCR_OUTPUT_XLSX)
    shutil.copy2(SNAPSHOT_DIR / db.PROPERTIES_XLSX.name, db.PROPERTIES_XLSX)
    ocr0 = db.read_ocr_output()
    props0 = db.read_properties()

    # --- preview sobre el estado stale restante ---
    p = preview()
    assert p["total_changes"] > 0
    print(f"[ok] preview: {p['properties_with_changes']} propiedades, {p['total_changes']} campos")

    # --- idempotencia: preview no modifica datos ---
    p2 = preview()
    assert p2["total_changes"] == p["total_changes"] and p2["properties_with_changes"] == p["properties_with_changes"]
    print("[ok] idempotencia: preview repetido devuelve mismos resultados")

    # --- caso sin cambios (datos ya iguales) ---
    # Seed a state where properties match OCR exactly
    props_clean = db.read_properties()
    ocr_clean = db.read_ocr_output().drop_duplicates("codigo", keep="last")
    # Apply OCR values to properties to make them match
    for _, row in ocr_clean.iterrows():
        codigo = str(int(row["codigo"]))
        updates = {}
        for field in FIELDS:
            if field in row and not pd.isna(row[field]):
                updates[field] = row[field]
        if updates:
            db.update_property(codigo, updates)
    props_matched = db.read_properties()
    assert build_changes(props_matched, ocr_clean) == []
    print("[ok] sin cambios: current == OCR -> sin correcciones")


def main() -> None:
    # Seed stale first, then snapshot that state
    seed_stale()
    snapshot()
    print(f"[setup] snapshot en {SNAPSHOT_DIR}")
    try:
        run_checks()
    finally:
        restore()
    print("AUTOMATION TESTS: PASS")


if __name__ == "__main__":
    main()