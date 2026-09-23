"""Validation tests for the automation_system Playwright flow (no browser).

Run with the project venv:

    venv/Scripts/python.exe -m automation_system.backend.tests.test_playwright_validation

Follows the inline launcher convention (no pytest dependency). shared_store
workbooks are snapshotted first and restored unconditionally in ``finally``.

Covers every path that does NOT require a real browser or the running Target
System stack: endpoint existence, invalid field (422), missing property (404)
and the no-change case (stage='no_change', no browser). The demo property is
picked dynamically from the shared data (any property present in both
properties_db and ocr_output) so the test never depends on a specific seeded
code. The live E2E (driving http://127.0.0.1:5173) requires Target UI + Target
backend + Automation backend up and is exercised manually / documented in the
README.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from automation_system.backend.main import app  # noqa: E402
from automation_system.backend.services import playwright_automation as pw_svc  # noqa: E402
from shared_store import db  # noqa: E402

FIELD = "superficie_m2"
SNAPSHOT_DIR = Path(os.environ["TEMP"]) / f"playwright_validation_{os.getpid()}"

client = TestClient(app)


def pick_target_codigo() -> str:
    """A property that exists in both the property store and the OCR output."""
    propiedades = db.read_properties()
    ocr = db.read_ocr_output()
    assert not ocr.empty and "codigo" in ocr.columns
    ocr_codes: set[str] = set(ocr["codigo"].astype(str))
    codes = [c for c in propiedades["codigo"].astype(str) if c in ocr_codes]
    assert codes, "no hay una propiedad compartida entre properties_db y ocr_output"
    assert FIELD in ocr.columns, f"campo {FIELD} no presente en ocr_output"
    return codes[0]


TARGET_CODIGO = pick_target_codigo()


def snapshot() -> None:
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    for f in (db.PROPERTIES_XLSX, db.GROUND_TRUTH_XLSX, db.OCR_OUTPUT_XLSX):
        shutil.copy2(f, SNAPSHOT_DIR / f.name)


def restore() -> None:
    for f in (db.PROPERTIES_XLSX, db.GROUND_TRUTH_XLSX, db.OCR_OUTPUT_XLSX):
        shutil.copy2(SNAPSHOT_DIR / f.name, f)
    print("[restore] shared_store restaurado al snapshot")


def run_checks() -> None:
    # --- 1. single endpoint exists ------------------------------------------
    r = client.post("/api/automation/playwright", json={})
    assert r.status_code == 422, r.text  # route exists: pydantic validation fires
    print("[ok] endpoint POST /api/automation/playwright existe (validacion 422)")

    # --- 2. invalid field rejected (422) ------------------------------------
    r = client.post("/api/automation/playwright", json={"codigo": TARGET_CODIGO, "field": "direccion"})
    assert r.status_code == 422, r.text
    print("[ok] campo invalido rechazado  (status=%s)" % r.status_code)

    # --- 3. missing property rejected (404) ---------------------------------
    r = client.post("/api/automation/playwright", json={"codigo": "999999", "field": FIELD})
    assert r.status_code == 404, r.text
    print("[ok] propiedad inexistente rechazada (status=%s)" % r.status_code)

    # --- 4. no-change case: rejected safely, no browser ---------------------
    ocr = db.read_ocr_output()
    assert "codigo" in ocr.columns and not ocr.empty
    ocr_norm = ocr.drop_duplicates("codigo", keep="last")
    # Force ALL fields to match OCR so there are no pending changes
    ocr_row = ocr_norm.loc[ocr_norm["codigo"].astype(str) == TARGET_CODIGO].iloc[0]
    updates = {f: ocr_row[f] for f in db.NUMERIC_FIELDS if f in ocr_row and not pd.isna(ocr_row[f])}
    db.update_property(TARGET_CODIGO, updates)
    result = pw_svc.apply_correction(TARGET_CODIGO, FIELD)
    assert result["success"] is False and result["stage"] == "no_change", result
    assert result["steps"] == []
    print("[ok] sin cambios -> escenario no_change (sin abrir browser)")

    # --- 5. batch endpoint exists -------------------------------------------
    r = client.post("/api/automation/playwright/batch", json={})
    assert r.status_code == 422, r.text  # route exists: pydantic fires
    r = client.post("/api/automation/playwright/batch", json={"codigos": []})
    assert r.status_code == 422, r.text
    print("[ok] endpoint POST /api/automation/playwright/batch existe (422 sin codigos)")

    # --- 6. batch invalid field rejected (422) -------------------------------
    r = client.post("/api/automation/playwright/batch", json={"codigos": [TARGET_CODIGO], "field": "direccion"})
    assert r.status_code == 422, r.text
    print("[ok] batch field invalido rechazado (status=%s)" % r.status_code)

    # --- 7. batch missing property rejected (404) ----------------------------
    r = client.post("/api/automation/playwright/batch", json={"codigos": ["999999"]})
    assert r.status_code == 404, r.text
    print("[ok] batch propiedad inexistente rechazada (status=%s)" % r.status_code)

    # --- 8. batch no-change: no browser, every result no_change --------------
    batch = pw_svc.apply_corrections([TARGET_CODIGO], FIELD)
    assert batch["steps"] == [], batch
    assert batch["success"] is False and batch["failed"] == 0, batch
    assert len(batch["results"]) == 1
    assert batch["results"][0]["stage"] == "no_change", batch["results"]
    print("[ok] batch sin cambios -> no_change por propiedad, browser nunca abierto")

    # --- 9. headless override accepted ---------------------------------------
    batch_h = pw_svc.apply_corrections([TARGET_CODIGO], FIELD, headless=True)
    assert batch_h["steps"] == [] and batch_h["results"][0]["stage"] == "no_change"
    r = client.post(
        "/api/automation/playwright/batch",
        json={"codigos": [TARGET_CODIGO], "field": FIELD, "headless": True},
    )
    assert r.status_code == 200, r.text
    assert r.json()["results"][0]["stage"] == "no_change"
    print("[ok] headless override aceptado en servicio y API (no_change, sin browser)")


def main() -> None:
    snapshot()
    print(f"[setup] snapshot en {SNAPSHOT_DIR}")
    try:
        run_checks()
    finally:
        restore()
    print("PLAYWRIGHT VALIDATION TESTS: PASS")


if __name__ == "__main__":
    main()